package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/bizpulse/transaction-svc/internal/auth"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

type contextKey string

const (
	ClaimsKey contextKey = "claims"
)

// Auth creates a dual-mode authentication middleware.
// Mode 1 (Kong path): If X-User-Id header is present, Kong has already validated
// the JWT. Trust the forwarded headers (X-User-Id, X-Business-Id, X-Roles).
// Mode 2 (Legacy path): If no Kong headers, fall back to HS256 JWT validation.
// This dual-mode approach allows a gradual migration to Keycloak/Kong (ADR-0017).
func Auth(secret string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Kong-forwarded path: headers already verified by Kong JWT plugin
			if uid := r.Header.Get("X-User-Id"); uid != "" {
				userID, err := uuid.Parse(uid)
				if err != nil {
					http.Error(w, `{"error":{"code":"UNAUTHORIZED","message":"invalid X-User-Id header"}}`, http.StatusUnauthorized)
					return
				}
				businessID := uuid.Nil
				if bid := r.Header.Get("X-Business-Id"); bid != "" {
					businessID, _ = uuid.Parse(bid)
				}
				claims := &auth.Claims{
					RegisteredClaims: jwt.RegisteredClaims{Subject: userID.String()},
					BusinessID:       businessID,
					Role:             r.Header.Get("X-Roles"),
				}
				ctx := context.WithValue(r.Context(), ClaimsKey, claims)
				next.ServeHTTP(w, r.WithContext(ctx))
				return
			}

			// Legacy HS256 JWT path
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
