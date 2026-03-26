package config

import (
	"fmt"
	"os"
	"strconv"
)

type Config struct {
	Port           string
	PostgresDSN    string
	JWTSecret      string
	JWTExpiryHours int
	AllowedOrigins string
	MaxBodyBytes   int64
}

func Load() (*Config, error) {
	jwtSecret := getEnv("JWT_SECRET", "")
	if jwtSecret == "" {
		return nil, fmt.Errorf("JWT_SECRET is required and must not be empty")
	}
	if len(jwtSecret) < 32 {
		return nil, fmt.Errorf("JWT_SECRET must be at least 32 characters")
	}

	jwtExpiry, err := strconv.Atoi(getEnv("JWT_EXPIRY_HOURS", "24"))
	if err != nil {
		return nil, fmt.Errorf("invalid JWT_EXPIRY_HOURS: %w", err)
	}

	host := getEnv("POSTGRES_HOST", "localhost")
	port := getEnv("POSTGRES_PORT", "5432")
	db := getEnv("POSTGRES_DB", "bizpulse")
	user := getEnv("POSTGRES_USER", "bizpulse")
	pass := getEnv("POSTGRES_PASSWORD", "")
	sslmode := getEnv("POSTGRES_SSLMODE", "disable")

	dsn := fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=%s", user, pass, host, port, db, sslmode)

	return &Config{
		Port:           getEnv("TRANSACTION_SVC_PORT", "8080"),
		PostgresDSN:    dsn,
		JWTSecret:      jwtSecret,
		JWTExpiryHours: jwtExpiry,
		AllowedOrigins: getEnv("ALLOWED_ORIGINS", "http://localhost:3000"),
		MaxBodyBytes:   1_048_576, // 1MB
	}, nil
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
