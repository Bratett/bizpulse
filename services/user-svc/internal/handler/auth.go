package handler

import (
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"strings"

	"github.com/bizpulse/user-svc/internal/keycloak"
	"github.com/bizpulse/user-svc/internal/model"
	"github.com/bizpulse/user-svc/internal/repository"
)

type AuthHandler struct {
	userRepo     *repository.UserRepo
	auditRepo    *repository.AuditRepo
	kcClient     *keycloak.Client
	maxBodyBytes int64
}

func NewAuthHandler(
	userRepo *repository.UserRepo,
	auditRepo *repository.AuditRepo,
	kcClient *keycloak.Client,
	maxBodyBytes int64,
) *AuthHandler {
	return &AuthHandler{
		userRepo:     userRepo,
		auditRepo:    auditRepo,
		kcClient:     kcClient,
		maxBodyBytes: maxBodyBytes,
	}
}

// Register handles POST /v1/auth/register.
// Flow:
//  1. Validate input (email format, password strength >=8 chars, required fields)
//  2. Create user in Keycloak via Admin API
//  3. Insert user, business, membership records in one DB transaction
//  4. Set business_id as Keycloak user attribute
//  5. Get initial tokens from Keycloak token endpoint
//  6. Write audit_log entry
//  7. Return tokens + user + business
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

	// Step 1: Create user in Keycloak
	keycloakUserID, err := h.kcClient.CreateUser(req.Email, req.Password, req.FirstName, req.LastName)
	if err != nil {
		if strings.Contains(err.Error(), "already exists") {
			writeError(w, http.StatusConflict, "EMAIL_EXISTS", "This email is already registered")
			return
		}
		log.Printf("ERROR: keycloak create user: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Registration failed")
		return
	}

	// Step 2: Insert user, business, membership in DB
	user, biz, err := h.userRepo.Register(r.Context(), req, keycloakUserID)
	if err != nil {
		if errors.Is(err, repository.ErrEmailExists) {
			writeError(w, http.StatusConflict, "EMAIL_EXISTS", "This email is already registered")
			return
		}
		log.Printf("ERROR: db register: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Registration failed")
		return
	}

	// Step 3: Set business_id as Keycloak user attribute (non-blocking)
	if err := h.kcClient.SetUserAttribute(keycloakUserID, "business_id", biz.ID.String()); err != nil {
		log.Printf("WARN: set keycloak business_id attribute: %v", err)
	}

	// Step 4: Get initial tokens from Keycloak
	tokenResp, err := h.kcClient.GetToken(req.Email, req.Password)
	if err != nil {
		log.Printf("ERROR: keycloak get token after registration: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Registration succeeded but token generation failed")
		return
	}

	// Step 5: Audit log (non-critical — warn only)
	if err := h.auditRepo.Log(r.Context(), &biz.ID, &user.ID, "user", user.ID, "user.registered", user); err != nil {
		log.Printf("WARN: audit log failed for registration: %v", err)
	}

	// Step 6: Return response
	writeJSON(w, http.StatusCreated, model.AuthResponse{
		AccessToken:  tokenResp.AccessToken,
		RefreshToken: tokenResp.RefreshToken,
		TokenType:    tokenResp.TokenType,
		ExpiresIn:    tokenResp.ExpiresIn,
		User:         *user,
		Business:     *biz,
	})
}

// Login handles POST /v1/auth/login.
// Delegates credential validation entirely to Keycloak's token endpoint.
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

	// Authenticate via Keycloak token endpoint
	tokenResp, err := h.kcClient.GetToken(email, req.Password)
	if err != nil {
		if strings.Contains(err.Error(), "401") || strings.Contains(err.Error(), "Invalid") {
			writeError(w, http.StatusUnauthorized, "INVALID_CREDENTIALS", "Invalid email or password")
			return
		}
		log.Printf("ERROR: keycloak login: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Login failed")
		return
	}

	// Look up user and business from local DB for the response
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

	biz, _, err := h.userRepo.GetBusinessForUser(r.Context(), user.ID)
	if err != nil || biz == nil {
		log.Printf("ERROR: get business: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Login failed")
		return
	}

	writeJSON(w, http.StatusOK, model.AuthResponse{
		AccessToken:  tokenResp.AccessToken,
		RefreshToken: tokenResp.RefreshToken,
		TokenType:    tokenResp.TokenType,
		ExpiresIn:    tokenResp.ExpiresIn,
		User:         *user,
		Business:     *biz,
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
