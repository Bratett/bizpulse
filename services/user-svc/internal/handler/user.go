package handler

import (
	"log"
	"net/http"

	"github.com/bizpulse/user-svc/internal/middleware"
	"github.com/bizpulse/user-svc/internal/model"
	"github.com/bizpulse/user-svc/internal/repository"
)

type UserHandler struct {
	userRepo     *repository.UserRepo
	auditRepo    *repository.AuditRepo
	maxBodyBytes int64
}

func NewUserHandler(userRepo *repository.UserRepo, auditRepo *repository.AuditRepo, maxBodyBytes int64) *UserHandler {
	return &UserHandler{
		userRepo:     userRepo,
		auditRepo:    auditRepo,
		maxBodyBytes: maxBodyBytes,
	}
}

// GetMe handles GET /v1/users/me.
// Returns the authenticated user's profile.
func (h *UserHandler) GetMe(w http.ResponseWriter, r *http.Request) {
	userID, ok := middleware.GetUserID(r.Context())
	if !ok {
		writeError(w, http.StatusUnauthorized, "UNAUTHORIZED", "Authentication required")
		return
	}

	user, err := h.userRepo.FindByID(r.Context(), userID)
	if err != nil {
		log.Printf("ERROR: find user: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to fetch user")
		return
	}
	if user == nil {
		writeError(w, http.StatusNotFound, "NOT_FOUND", "User not found")
		return
	}

	writeJSON(w, http.StatusOK, model.UserResponse{
		ID:                user.ID,
		Email:             user.Email,
		FirstName:         user.FirstName,
		LastName:          user.LastName,
		PreferredLanguage: user.PreferredLanguage,
		Status:            user.Status,
	})
}

// UpdateMe handles PATCH /v1/users/me.
// Partially updates the authenticated user's profile.
func (h *UserHandler) UpdateMe(w http.ResponseWriter, r *http.Request) {
	userID, ok := middleware.GetUserID(r.Context())
	if !ok {
		writeError(w, http.StatusUnauthorized, "UNAUTHORIZED", "Authentication required")
		return
	}

	r.Body = http.MaxBytesReader(w, r.Body, h.maxBodyBytes)

	var req model.UpdateUserRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Validate at least one field is provided
	if req.FirstName == nil && req.LastName == nil && req.PreferredLanguage == nil {
		writeError(w, http.StatusBadRequest, "VALIDATION_ERROR", "At least one field must be provided")
		return
	}

	// Validate preferred_language if provided
	if req.PreferredLanguage != nil {
		lang := *req.PreferredLanguage
		validLangs := map[string]bool{"en": true, "tw": true, "ee": true, "ga": true, "dag": true, "ha": true}
		if !validLangs[lang] {
			writeError(w, http.StatusBadRequest, "VALIDATION_ERROR", "Unsupported language. Supported: en, tw, ee, ga, dag, ha")
			return
		}
	}

	user, err := h.userRepo.Update(r.Context(), userID, req)
	if err != nil {
		log.Printf("ERROR: update user: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to update user")
		return
	}
	if user == nil {
		writeError(w, http.StatusNotFound, "NOT_FOUND", "User not found")
		return
	}

	// Audit log (non-critical)
	if err := h.auditRepo.Log(r.Context(), nil, &userID, "user", userID, "user.updated", user); err != nil {
		log.Printf("WARN: audit log failed for user update: %v", err)
	}

	writeJSON(w, http.StatusOK, model.UserResponse{
		ID:                user.ID,
		Email:             user.Email,
		FirstName:         user.FirstName,
		LastName:          user.LastName,
		PreferredLanguage: user.PreferredLanguage,
		Status:            user.Status,
	})
}
