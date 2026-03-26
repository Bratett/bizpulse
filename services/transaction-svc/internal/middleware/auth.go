package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/bizpulse/transaction-svc/internal/auth"
)

type contextKey string

const (
	ClaimsKey contextKey = "claims"
)

func Auth(secret string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			tokenStr := extractToken(r)
			if tokenStr == "" {
				http.Error(w, `{"error":{"code":"UNAUTHORIZED","message":"missing or invalid authorization header"}}`, http.StatusUnauthorized)
				return
			}

			claims, err := auth.ValidateToken(secret, tokenStr)
			if err != nil {
				http.Error(w, `{"error":{"code":"UNAUTHORIZED","message":"invalid or expired token"}}`, http.StatusUnauthorized)
				return
			}

			ctx := context.WithValue(r.Context(), ClaimsKey, claims)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func GetClaims(ctx context.Context) *auth.Claims {
	claims, _ := ctx.Value(ClaimsKey).(*auth.Claims)
	return claims
}

func extractToken(r *http.Request) string {
	// Check Authorization header
	bearer := r.Header.Get("Authorization")
	if strings.HasPrefix(bearer, "Bearer ") {
		return strings.TrimPrefix(bearer, "Bearer ")
	}

	// Check cookie
	cookie, err := r.Cookie("token")
	if err == nil {
		return cookie.Value
	}

	return ""
}
