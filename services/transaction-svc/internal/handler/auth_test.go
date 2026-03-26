package handler

import (
	"testing"

	"github.com/bizpulse/transaction-svc/internal/model"
)

func TestValidateRegisterRequest(t *testing.T) {
	validReq := model.RegisterRequest{
		Email:        "test@example.com",
		Password:     "securepass123",
		FirstName:    "Kwame",
		LastName:     "Asante",
		BusinessName: "Asante Enterprises",
	}

	t.Run("valid request returns no errors", func(t *testing.T) {
		errs := validateRegisterRequest(validReq)
		if len(errs) != 0 {
			t.Errorf("expected no errors, got %v", errs)
		}
	})

	t.Run("missing email", func(t *testing.T) {
		req := validReq
		req.Email = ""
		errs := validateRegisterRequest(req)
		if _, ok := errs["email"]; !ok {
			t.Error("expected email error, got none")
		}
	})

	t.Run("invalid email format no at sign", func(t *testing.T) {
		req := validReq
		req.Email = "notanemail"
		errs := validateRegisterRequest(req)
		if _, ok := errs["email"]; !ok {
			t.Error("expected email format error, got none")
		}
	})

	t.Run("invalid email format no dot", func(t *testing.T) {
		req := validReq
		req.Email = "user@domain"
		errs := validateRegisterRequest(req)
		if _, ok := errs["email"]; !ok {
			t.Error("expected email format error for missing dot, got none")
		}
	})

	t.Run("missing password", func(t *testing.T) {
		req := validReq
		req.Password = ""
		errs := validateRegisterRequest(req)
		if _, ok := errs["password"]; !ok {
			t.Error("expected password error, got none")
		}
	})

	t.Run("password too short", func(t *testing.T) {
		req := validReq
		req.Password = "short"
		errs := validateRegisterRequest(req)
		if _, ok := errs["password"]; !ok {
			t.Error("expected password length error, got none")
		}
	})

	t.Run("password exactly 7 chars", func(t *testing.T) {
		req := validReq
		req.Password = "1234567"
		errs := validateRegisterRequest(req)
		if _, ok := errs["password"]; !ok {
			t.Error("expected password length error for 7 chars, got none")
		}
	})

	t.Run("password exactly 8 chars is valid", func(t *testing.T) {
		req := validReq
		req.Password = "12345678"
		errs := validateRegisterRequest(req)
		if _, ok := errs["password"]; ok {
			t.Error("password of 8 chars should be valid")
		}
	})

	t.Run("missing first_name", func(t *testing.T) {
		req := validReq
		req.FirstName = ""
		errs := validateRegisterRequest(req)
		if _, ok := errs["first_name"]; !ok {
			t.Error("expected first_name error, got none")
		}
	})

	t.Run("first_name whitespace only", func(t *testing.T) {
		req := validReq
		req.FirstName = "   "
		errs := validateRegisterRequest(req)
		if _, ok := errs["first_name"]; !ok {
			t.Error("expected first_name error for whitespace-only, got none")
		}
	})

	t.Run("missing last_name", func(t *testing.T) {
		req := validReq
		req.LastName = ""
		errs := validateRegisterRequest(req)
		if _, ok := errs["last_name"]; !ok {
			t.Error("expected last_name error, got none")
		}
	})

	t.Run("last_name whitespace only", func(t *testing.T) {
		req := validReq
		req.LastName = "   "
		errs := validateRegisterRequest(req)
		if _, ok := errs["last_name"]; !ok {
			t.Error("expected last_name error for whitespace-only, got none")
		}
	})

	t.Run("missing business_name", func(t *testing.T) {
		req := validReq
		req.BusinessName = ""
		errs := validateRegisterRequest(req)
		if _, ok := errs["business_name"]; !ok {
			t.Error("expected business_name error, got none")
		}
	})

	t.Run("business_name whitespace only", func(t *testing.T) {
		req := validReq
		req.BusinessName = "   "
		errs := validateRegisterRequest(req)
		if _, ok := errs["business_name"]; !ok {
			t.Error("expected business_name error for whitespace-only, got none")
		}
	})

	t.Run("multiple missing fields", func(t *testing.T) {
		req := model.RegisterRequest{}
		errs := validateRegisterRequest(req)
		expectedFields := []string{"email", "password", "first_name", "last_name", "business_name"}
		for _, field := range expectedFields {
			if _, ok := errs[field]; !ok {
				t.Errorf("expected error for %q, got none", field)
			}
		}
	})
}

func TestValidateRegisterRequest_EmailNormalization(t *testing.T) {
	// The Register handler normalizes email before calling validate.
	// We test that the validation function itself accepts normalized emails
	// and rejects invalid ones. The normalization (ToLower + TrimSpace)
	// happens in the handler, not in validateRegisterRequest.

	t.Run("lowercase email is valid", func(t *testing.T) {
		req := model.RegisterRequest{
			Email:        "user@example.com",
			Password:     "securepass123",
			FirstName:    "Kwame",
			LastName:     "Asante",
			BusinessName: "Test Biz",
		}
		errs := validateRegisterRequest(req)
		if _, ok := errs["email"]; ok {
			t.Error("lowercase email should be valid")
		}
	})

	t.Run("email with plus addressing is valid", func(t *testing.T) {
		req := model.RegisterRequest{
			Email:        "user+tag@example.com",
			Password:     "securepass123",
			FirstName:    "Kwame",
			LastName:     "Asante",
			BusinessName: "Test Biz",
		}
		errs := validateRegisterRequest(req)
		if _, ok := errs["email"]; ok {
			t.Error("email with plus addressing should be valid")
		}
	})

	t.Run("email with subdomain is valid", func(t *testing.T) {
		req := model.RegisterRequest{
			Email:        "user@mail.example.com",
			Password:     "securepass123",
			FirstName:    "Kwame",
			LastName:     "Asante",
			BusinessName: "Test Biz",
		}
		errs := validateRegisterRequest(req)
		if _, ok := errs["email"]; ok {
			t.Error("email with subdomain should be valid")
		}
	})
}
