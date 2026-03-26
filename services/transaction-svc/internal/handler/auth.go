package handler

import (
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"strings"

	"github.com/bizpulse/transaction-svc/internal/auth"
	"github.com/bizpulse/transaction-svc/internal/model"
	"github.com/bizpulse/transaction-svc/internal/repository"
	"golang.org/x/crypto/bcrypt"
)

type AuthHandler struct {
	userRepo     *repository.UserRepo
	auditRepo    *repository.AuditRepo
	jwtSecret    string
	jwtExpiry    int
	maxBodyBytes int64
}

func NewAuthHandler(userRepo *repository.UserRepo, auditRepo *repository.AuditRepo, jwtSecret string, jwtExpiry int, maxBodyBytes int64) *AuthHandler {
	return &AuthHandler{
		userRepo:     userRepo,
		auditRepo:    auditRepo,
		jwtSecret:    jwtSecret,
		jwtExpiry:    jwtExpiry,
		maxBodyBytes: maxBodyBytes,
	}
}

func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	r.Body = http.MaxBytesReader(w, r.Body, h.maxBodyBytes)

	var req model.RegisterRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Normalize email
	req.Email = strings.ToLower(strings.TrimSpace(req.Email))

	if errs := validateRegisterRequest(req); len(errs) > 0 {
		writeErrorWithDetails(w, http.StatusBadRequest, "VALIDATION_ERROR", "Validation failed", errs)
		return
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), 12)
	if err != nil {
		log.Printf("ERROR: hash password: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Registration failed")
		return
	}

	user, biz, err := h.userRepo.Register(r.Context(), req, string(hash))
	if err != nil {
		if errors.Is(err, repository.ErrEmailExists) {
			writeError(w, http.StatusConflict, "EMAIL_EXISTS", "This email is already registered")
			return
		}
		log.Printf("ERROR: register: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Registration failed")
		return
	}

	// Audit log (non-critical for registration — warn only)
	if err := h.auditRepo.Log(r.Context(), &biz.ID, &user.ID, "user", user.ID, "user.registered", user); err != nil {
		log.Printf("WARN: audit log failed for registration: %v", err)
	}

	token, err := auth.GenerateToken(h.jwtSecret, user.ID, biz.ID, "owner", h.jwtExpiry)
	if err != nil {
		log.Printf("ERROR: generate token: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Registration succeeded but token generation failed")
		return
	}

	setTokenCookie(w, token, h.jwtExpiry)

	writeJSON(w, http.StatusCreated, model.AuthResponse{
		Token:    token,
		User:     *user,
		Business: *biz,
	})
}

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	r.Body = http.MaxBytesReader(w, r.Body, h.maxBodyBytes)

	var req model.LoginRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	if req.Email == "" || req.Password == "" {
		writeError(w, http.StatusBadRequest, "VALIDATION_ERROR", "Email and password are required")
		return
	}

	email := strings.ToLower(strings.TrimSpace(req.Email))

	user, err := h.userRepo.FindByEmail(r.Context(), email)
	if err != nil {
		log.Printf("ERROR: find user: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Login failed")
		return
	}
	if user == nil {
		writeError(w, http.StatusUnauthorized, "INVALID_CREDENTIALS", "Invalid email or password")
		return
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
		writeError(w, http.StatusUnauthorized, "INVALID_CREDENTIALS", "Invalid email or password")
		return
	}

	biz, role, err := h.userRepo.GetBusinessForUser(r.Context(), user.ID)
	if err != nil || biz == nil {
		log.Printf("ERROR: get business: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Login failed")
		return
	}

	token, err := auth.GenerateToken(h.jwtSecret, user.ID, biz.ID, role, h.jwtExpiry)
	if err != nil {
		log.Printf("ERROR: generate token: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Login failed")
		return
	}

	setTokenCookie(w, token, h.jwtExpiry)

	writeJSON(w, http.StatusOK, model.AuthResponse{
		Token:    token,
		User:     *user,
		Business: *biz,
	})
}

func setTokenCookie(w http.ResponseWriter, token string, expiryHours int) {
	http.SetCookie(w, &http.Cookie{
		Name:     "token",
		Value:    token,
		Path:     "/",
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
		MaxAge:   expiryHours * 3600,
	})
}

func validateRegisterRequest(req model.RegisterRequest) map[string]string {
	errs := make(map[string]string)

	if req.Email == "" {
		errs["email"] = "Email is required"
	} else if !strings.Contains(req.Email, "@") || !strings.Contains(req.Email, ".") {
		errs["email"] = "Invalid email format"
	}

	if req.Password == "" {
		errs["password"] = "Password is required"
	} else if len(req.Password) < 8 {
		errs["password"] = "Password must be at least 8 characters"
	}

	if strings.TrimSpace(req.FirstName) == "" {
		errs["first_name"] = "First name is required"
	}

	if strings.TrimSpace(req.LastName) == "" {
		errs["last_name"] = "Last name is required"
	}

	if strings.TrimSpace(req.BusinessName) == "" {
		errs["business_name"] = "Business name is required"
	}

	return errs
}

// JSON helpers (API_CONTRACT.md section 5.3 error envelope)

func decodeJSON(r *http.Request, v any) error {
	return json.NewDecoder(r.Body).Decode(v)
}

func writeJSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

func writeError(w http.ResponseWriter, status int, code, message string) {
	writeJSON(w, status, model.ErrorResponse{
		Error: model.ErrorDetail{Code: code, Message: message},
	})
}

func writeErrorWithDetails(w http.ResponseWriter, status int, code, message string, details any) {
	writeJSON(w, status, model.ErrorResponse{
		Error: model.ErrorDetail{Code: code, Message: message, Details: details},
	})
}
