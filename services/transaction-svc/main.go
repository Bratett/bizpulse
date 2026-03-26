package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/bizpulse/transaction-svc/internal/config"
	"github.com/bizpulse/transaction-svc/internal/db"
	"github.com/bizpulse/transaction-svc/internal/handler"
	"github.com/bizpulse/transaction-svc/internal/middleware"
	"github.com/bizpulse/transaction-svc/internal/repository"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	pool, err := db.NewPool(ctx, cfg.PostgresDSN)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	// Repositories
	userRepo := repository.NewUserRepo(pool)
	auditRepo := repository.NewAuditRepo(pool)
	txnRepo := repository.NewTransactionRepo(pool)

	// Handlers
	authHandler := handler.NewAuthHandler(userRepo, auditRepo, cfg.JWTSecret, cfg.JWTExpiryHours, cfg.MaxBodyBytes)
	txnHandler := handler.NewTransactionHandler(txnRepo, cfg.MaxBodyBytes)

	// Middleware
	authMw := middleware.Auth(cfg.JWTSecret)
	cors := middleware.CORS(cfg.AllowedOrigins)
	authRateLimit := middleware.RateLimit(5, 15*time.Minute)

	// Routes
	mux := http.NewServeMux()

	// Health check (public) — verifies DB connectivity
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		if err := pool.Ping(r.Context()); err != nil {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusServiceUnavailable)
			fmt.Fprintf(w, `{"status":"unhealthy","service":"transaction-svc","error":"database unreachable"}`)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"status":"ok","service":"transaction-svc"}`)
	})

	// Auth routes (public, rate-limited)
	mux.HandleFunc("POST /v1/auth/register", authRateLimit(authHandler.Register))
	mux.HandleFunc("POST /v1/auth/login", authRateLimit(authHandler.Login))

	// Transaction routes (authenticated)
	mux.Handle("POST /v1/transactions", authMw(http.HandlerFunc(txnHandler.Create)))
	mux.Handle("GET /v1/transactions", authMw(http.HandlerFunc(txnHandler.List)))

	// Chart of accounts (authenticated)
	mux.Handle("GET /v1/accounts", authMw(http.HandlerFunc(txnHandler.ListAccounts)))

	srv := &http.Server{
		Addr:         ":" + cfg.Port,
		Handler:      cors(mux),
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful shutdown — drain requests THEN close pool
	go func() {
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
		<-sigCh
		log.Println("Shutting down...")
		shutCtx, shutCancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer shutCancel()
		srv.Shutdown(shutCtx)
		pool.Close()
	}()

	log.Printf("Transaction service starting on :%s", cfg.Port)
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("Server failed: %v", err)
	}
}
