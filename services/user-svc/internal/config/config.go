package config

import (
	"fmt"
	"os"
)

type Config struct {
	Port                 string
	PostgresDSN          string
	KeycloakAdminURL     string
	KeycloakRealm        string
	KeycloakClientID     string
	KeycloakClientSecret string
	AllowedOrigins       string
	MaxBodyBytes         int64
}

func Load() (*Config, error) {
	clientID := getEnv("KEYCLOAK_CLIENT_ID", "")
	if clientID == "" {
		return nil, fmt.Errorf("KEYCLOAK_CLIENT_ID is required")
	}

	clientSecret := getEnv("KEYCLOAK_CLIENT_SECRET", "")
	if clientSecret == "" {
		return nil, fmt.Errorf("KEYCLOAK_CLIENT_SECRET is required")
	}

	host := getEnv("POSTGRES_HOST", "localhost")
	port := getEnv("POSTGRES_PORT", "5432")
	db := getEnv("POSTGRES_DB", "bizpulse")
	user := getEnv("POSTGRES_USER", "bizpulse")
	pass := getEnv("POSTGRES_PASSWORD", "")
	sslmode := getEnv("POSTGRES_SSLMODE", "disable")

	dsn := fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=%s", user, pass, host, port, db, sslmode)

	return &Config{
		Port:                 getEnv("USER_SVC_PORT", "8083"),
		PostgresDSN:          dsn,
		KeycloakAdminURL:     getEnv("KEYCLOAK_ADMIN_URL", "http://keycloak:8080"),
		KeycloakRealm:        getEnv("KEYCLOAK_REALM", "bizpulse"),
		KeycloakClientID:     clientID,
		KeycloakClientSecret: clientSecret,
		AllowedOrigins:       getEnv("ALLOWED_ORIGINS", "http://localhost:3000"),
		MaxBodyBytes:         1_048_576, // 1MB
	}, nil
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
