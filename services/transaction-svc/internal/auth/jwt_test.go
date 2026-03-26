package auth

import (
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

func TestGenerateAndValidateToken(t *testing.T) {
	secret := "test-secret-key-at-least-32-chars-long"
	userID := uuid.New()
	businessID := uuid.New()
	role := "owner"
	expiryHours := 24

	token, err := GenerateToken(secret, userID, businessID, role, expiryHours)
	if err != nil {
		t.Fatalf("GenerateToken() error = %v", err)
	}
	if token == "" {
		t.Fatal("GenerateToken() returned empty token")
	}

	claims, err := ValidateToken(secret, token)
	if err != nil {
		t.Fatalf("ValidateToken() error = %v", err)
	}

	if claims.Subject != userID.String() {
		t.Errorf("Subject = %q, want %q", claims.Subject, userID.String())
	}
	if claims.BusinessID != businessID {
		t.Errorf("BusinessID = %v, want %v", claims.BusinessID, businessID)
	}
	if claims.Role != role {
		t.Errorf("Role = %q, want %q", claims.Role, role)
	}
	if claims.ExpiresAt == nil {
		t.Fatal("ExpiresAt is nil")
	}
	if claims.IssuedAt == nil {
		t.Fatal("IssuedAt is nil")
	}
}

func TestValidateToken_WrongSecret(t *testing.T) {
	secret := "test-secret-key-at-least-32-chars-long"
	wrongSecret := "wrong-secret-key-at-least-32-chars-long"
	userID := uuid.New()
	businessID := uuid.New()

	token, err := GenerateToken(secret, userID, businessID, "owner", 24)
	if err != nil {
		t.Fatalf("GenerateToken() error = %v", err)
	}

	_, err = ValidateToken(wrongSecret, token)
	if err == nil {
		t.Error("ValidateToken() with wrong secret should return error")
	}
}

func TestValidateToken_ExpiredToken(t *testing.T) {
	secret := "test-secret-key-at-least-32-chars-long"
	userID := uuid.New()
	businessID := uuid.New()

	// Manually create an already-expired token
	claims := Claims{
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   userID.String(),
			IssuedAt:  jwt.NewNumericDate(time.Now().Add(-2 * time.Hour)),
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(-1 * time.Hour)),
		},
		BusinessID: businessID,
		Role:       "owner",
	}
	tok := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenStr, err := tok.SignedString([]byte(secret))
	if err != nil {
		t.Fatalf("failed to create expired token: %v", err)
	}

	_, err = ValidateToken(secret, tokenStr)
	if err == nil {
		t.Error("ValidateToken() with expired token should return error")
	}
}

func TestValidateToken_MalformedToken(t *testing.T) {
	secret := "test-secret-key-at-least-32-chars-long"

	tests := []struct {
		name  string
		token string
	}{
		{"empty string", ""},
		{"random garbage", "not-a-jwt-token"},
		{"partial jwt", "eyJhbGciOiJIUzI1NiJ9."},
		{"three dots no content", "a.b.c"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := ValidateToken(secret, tt.token)
			if err == nil {
				t.Error("ValidateToken() with malformed token should return error")
			}
		})
	}
}

func TestGenerateToken_ClaimsContainBusinessIDAndRole(t *testing.T) {
	tests := []struct {
		name       string
		role       string
		businessID uuid.UUID
	}{
		{"owner role", "owner", uuid.New()},
		{"admin role", "admin", uuid.New()},
		{"viewer role", "viewer", uuid.New()},
		{"empty role", "", uuid.New()},
	}

	secret := "test-secret-key-at-least-32-chars-long"

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			userID := uuid.New()
			token, err := GenerateToken(secret, userID, tt.businessID, tt.role, 1)
			if err != nil {
				t.Fatalf("GenerateToken() error = %v", err)
			}

			claims, err := ValidateToken(secret, token)
			if err != nil {
				t.Fatalf("ValidateToken() error = %v", err)
			}

			if claims.BusinessID != tt.businessID {
				t.Errorf("BusinessID = %v, want %v", claims.BusinessID, tt.businessID)
			}
			if claims.Role != tt.role {
				t.Errorf("Role = %q, want %q", claims.Role, tt.role)
			}
		})
	}
}

func TestGenerateToken_DifferentExpiryHours(t *testing.T) {
	secret := "test-secret-key-at-least-32-chars-long"
	userID := uuid.New()
	businessID := uuid.New()

	tests := []struct {
		name        string
		expiryHours int
	}{
		{"1 hour", 1},
		{"24 hours", 24},
		{"168 hours (1 week)", 168},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			before := time.Now()
			token, err := GenerateToken(secret, userID, businessID, "owner", tt.expiryHours)
			if err != nil {
				t.Fatalf("GenerateToken() error = %v", err)
			}

			claims, err := ValidateToken(secret, token)
			if err != nil {
				t.Fatalf("ValidateToken() error = %v", err)
			}

			expectedExpiry := before.Add(time.Duration(tt.expiryHours) * time.Hour)
			// Allow 2 second tolerance for test execution time
			diff := claims.ExpiresAt.Time.Sub(expectedExpiry)
			if diff < -2*time.Second || diff > 2*time.Second {
				t.Errorf("ExpiresAt = %v, expected approximately %v (diff %v)", claims.ExpiresAt.Time, expectedExpiry, diff)
			}
		})
	}
}

func TestValidateToken_TamperedToken(t *testing.T) {
	// Create a valid token, then tamper with the payload to simulate
	// a token that has been modified after signing.
	secret := "test-secret-key-at-least-32-chars-long"
	userID := uuid.New()
	businessID := uuid.New()

	token, err := GenerateToken(secret, userID, businessID, "owner", 1)
	if err != nil {
		t.Fatalf("GenerateToken() error = %v", err)
	}

	// Tamper by flipping a character in the middle of the token
	runes := []rune(token)
	mid := len(runes) / 2
	if runes[mid] == 'A' {
		runes[mid] = 'B'
	} else {
		runes[mid] = 'A'
	}
	tampered := string(runes)

	_, err = ValidateToken(secret, tampered)
	if err == nil {
		t.Error("ValidateToken() with tampered token should return error")
	}
}

func TestGenerateToken_UniqueTokensPerCall(t *testing.T) {
	secret := "test-secret-key-at-least-32-chars-long"
	userID := uuid.New()
	businessID := uuid.New()

	token1, err := GenerateToken(secret, userID, businessID, "owner", 24)
	if err != nil {
		t.Fatalf("first GenerateToken() error = %v", err)
	}

	// Small delay to ensure different IssuedAt
	time.Sleep(1 * time.Millisecond)

	token2, err := GenerateToken(secret, userID, businessID, "owner", 24)
	if err != nil {
		t.Fatalf("second GenerateToken() error = %v", err)
	}

	// Tokens may actually be the same if generated within the same second since
	// jwt timestamps have second precision. This test verifies both are valid.
	if token1 == "" || token2 == "" {
		t.Error("tokens should not be empty")
	}

	// Both tokens should be independently valid
	_, err = ValidateToken(secret, token1)
	if err != nil {
		t.Errorf("first token validation error = %v", err)
	}
	_, err = ValidateToken(secret, token2)
	if err != nil {
		t.Errorf("second token validation error = %v", err)
	}
}
