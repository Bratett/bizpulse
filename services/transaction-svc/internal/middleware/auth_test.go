package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/bizpulse/transaction-svc/internal/auth"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

const testSecret = "test-secret-key-at-least-32-chars-long"

func TestAuth_ValidBearerToken(t *testing.T) {
	userID := uuid.New()
	businessID := uuid.New()
	role := "owner"

	token, err := auth.GenerateToken(testSecret, userID, businessID, role, 24)
	if err != nil {
		t.Fatalf("GenerateToken() error = %v", err)
	}

	var capturedClaims *auth.Claims
	handler := Auth(testSecret)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		capturedClaims = GetClaims(r.Context())
		w.WriteHeader(http.StatusOK)
	}))

	req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusOK)
	}
	if capturedClaims == nil {
		t.Fatal("claims should be set in context")
	}
	if capturedClaims.Subject != userID.String() {
		t.Errorf("Subject = %q, want %q", capturedClaims.Subject, userID.String())
	}
	if capturedClaims.BusinessID != businessID {
		t.Errorf("BusinessID = %v, want %v", capturedClaims.BusinessID, businessID)
	}
	if capturedClaims.Role != role {
		t.Errorf("Role = %q, want %q", capturedClaims.Role, role)
	}
}

func TestAuth_NoAuthorizationHeader(t *testing.T) {
	handler := Auth(testSecret)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called when no auth header present")
	}))

	req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusUnauthorized)
	}
}

func TestAuth_InvalidToken(t *testing.T) {
	handler := Auth(testSecret)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called with invalid token")
	}))

	tests := []struct {
		name   string
		header string
	}{
		{"garbage token", "Bearer not-a-valid-jwt"},
		{"wrong secret token", ""},
		{"empty bearer", "Bearer "},
		{"no bearer prefix", "Token abc123"},
		{"basic auth", "Basic dXNlcjpwYXNz"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
			if tt.header != "" {
				req.Header.Set("Authorization", tt.header)
			}
			rr := httptest.NewRecorder()

			handler.ServeHTTP(rr, req)

			if rr.Code != http.StatusUnauthorized {
				t.Errorf("status = %d, want %d", rr.Code, http.StatusUnauthorized)
			}
		})
	}
}

func TestAuth_WrongSecret(t *testing.T) {
	userID := uuid.New()
	businessID := uuid.New()

	// Generate token with different secret
	token, err := auth.GenerateToken("different-secret-at-least-32-chars!!", userID, businessID, "owner", 24)
	if err != nil {
		t.Fatalf("GenerateToken() error = %v", err)
	}

	handler := Auth(testSecret)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called with wrong-secret token")
	}))

	req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusUnauthorized)
	}
}

func TestAuth_ExpiredToken(t *testing.T) {
	userID := uuid.New()
	businessID := uuid.New()

	// Create an expired token manually
	claims := auth.Claims{
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   userID.String(),
			IssuedAt:  jwt.NewNumericDate(time.Now().Add(-2 * time.Hour)),
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(-1 * time.Hour)),
		},
		BusinessID: businessID,
		Role:       "owner",
	}
	tok := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenStr, err := tok.SignedString([]byte(testSecret))
	if err != nil {
		t.Fatalf("failed to create expired token: %v", err)
	}

	handler := Auth(testSecret)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called with expired token")
	}))

	req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
	req.Header.Set("Authorization", "Bearer "+tokenStr)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusUnauthorized)
	}
}

func TestAuth_CookieFallback(t *testing.T) {
	userID := uuid.New()
	businessID := uuid.New()
	role := "admin"

	token, err := auth.GenerateToken(testSecret, userID, businessID, role, 24)
	if err != nil {
		t.Fatalf("GenerateToken() error = %v", err)
	}

	var capturedClaims *auth.Claims
	handler := Auth(testSecret)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		capturedClaims = GetClaims(r.Context())
		w.WriteHeader(http.StatusOK)
	}))

	req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
	// No Authorization header; use cookie instead
	req.AddCookie(&http.Cookie{
		Name:  "token",
		Value: token,
	})
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusOK)
	}
	if capturedClaims == nil {
		t.Fatal("claims should be set from cookie token")
	}
	if capturedClaims.Subject != userID.String() {
		t.Errorf("Subject = %q, want %q", capturedClaims.Subject, userID.String())
	}
	if capturedClaims.Role != role {
		t.Errorf("Role = %q, want %q", capturedClaims.Role, role)
	}
}

func TestAuth_BearerTakesPrecedenceOverCookie(t *testing.T) {
	userID1 := uuid.New()
	businessID1 := uuid.New()
	userID2 := uuid.New()
	businessID2 := uuid.New()

	// Bearer token for user1
	bearerToken, err := auth.GenerateToken(testSecret, userID1, businessID1, "owner", 24)
	if err != nil {
		t.Fatalf("GenerateToken() for bearer error = %v", err)
	}

	// Cookie token for user2
	cookieToken, err := auth.GenerateToken(testSecret, userID2, businessID2, "viewer", 24)
	if err != nil {
		t.Fatalf("GenerateToken() for cookie error = %v", err)
	}

	var capturedClaims *auth.Claims
	handler := Auth(testSecret)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		capturedClaims = GetClaims(r.Context())
		w.WriteHeader(http.StatusOK)
	}))

	req := httptest.NewRequest(http.MethodGet, "/api/test", nil)
	req.Header.Set("Authorization", "Bearer "+bearerToken)
	req.AddCookie(&http.Cookie{
		Name:  "token",
		Value: cookieToken,
	})
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", rr.Code, http.StatusOK)
	}
	if capturedClaims == nil {
		t.Fatal("claims should be set")
	}
	// Bearer should take precedence: user1
	if capturedClaims.Subject != userID1.String() {
		t.Errorf("Subject = %q, want %q (bearer should take precedence)", capturedClaims.Subject, userID1.String())
	}
}

func TestGetClaims_NilContext(t *testing.T) {
	// GetClaims with a context that has no claims should return nil
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	claims := GetClaims(req.Context())
	if claims != nil {
		t.Error("GetClaims() should return nil when no claims in context")
	}
}

func TestExtractToken(t *testing.T) {
	tests := []struct {
		name       string
		authHeader string
		cookie     *http.Cookie
		wantEmpty  bool
	}{
		{
			name:       "bearer token",
			authHeader: "Bearer valid-token-string",
			wantEmpty:  false,
		},
		{
			name:      "cookie token",
			cookie:    &http.Cookie{Name: "token", Value: "cookie-token-string"},
			wantEmpty: false,
		},
		{
			name:      "no token at all",
			wantEmpty: true,
		},
		{
			name:       "wrong prefix",
			authHeader: "Basic dXNlcjpwYXNz",
			wantEmpty:  true,
		},
		{
			name:       "empty bearer",
			authHeader: "Bearer ",
			wantEmpty:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, "/", nil)
			if tt.authHeader != "" {
				req.Header.Set("Authorization", tt.authHeader)
			}
			if tt.cookie != nil {
				req.AddCookie(tt.cookie)
			}

			result := extractToken(req)

			if tt.wantEmpty && result != "" {
				t.Errorf("extractToken() = %q, want empty", result)
			}
			if !tt.wantEmpty && result == "" {
				t.Error("extractToken() returned empty, want non-empty")
			}
		})
	}
}
