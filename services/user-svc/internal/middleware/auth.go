package middleware

import (
	"context"
	"net/http"

	"github.com/google/uuid"
)

type contextKey string

const (
	UserIDKey     contextKey = "user_id"
	BusinessIDKey contextKey = "business_id"
	RolesKey      contextKey = "roles"
)

// Auth creates a Kong-header-only authentication middleware.
// Kong has already validated the JWT and forwarded identity headers.
// There is NO legacy JWT fallback — user-svc is Kong-only from day one.
func Auth() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			uid := r.Header.Get("X-User-Id")
			if uid == "" {
				http.Error(w, `{"error":{"code":"UNAUTHORIZED","message":"missing X-User-Id header"}}`, http.StatusUnauthorized)
				return
			}

			userID, err := uuid.Parse(uid)
			if err != nil {
				http.Error(w, `{"error":{"code":"UNAUTHORIZED","message":"invalid X-User-Id header"}}`, http.StatusUnauthorized)
				return
			}

			ctx := context.WithValue(r.Context(), UserIDKey, userID)

			if bid := r.Header.Get("X-Business-Id"); bid != "" {
				if businessID, err := uuid.Parse(bid); err == nil {
					ctx = context.WithValue(ctx, BusinessIDKey, businessID)
				}
			}

			if roles := r.Header.Get("X-Roles"); roles != "" {
				ctx = context.WithValue(ctx, RolesKey, roles)
			}

			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// GetUserID extracts the authenticated user ID from the request context.
func GetUserID(ctx context.Context) (uuid.UUID, bool) {
	id, ok := ctx.Value(UserIDKey).(uuid.UUID)
	return id, ok
}

// GetBusinessID extracts the business ID from the request context.
func GetBusinessID(ctx context.Context) (uuid.UUID, bool) {
	id, ok := ctx.Value(BusinessIDKey).(uuid.UUID)
	return id, ok
}

// GetRoles extracts the roles string from the request context.
func GetRoles(ctx context.Context) string {
	roles, _ := ctx.Value(RolesKey).(string)
	return roles
}
