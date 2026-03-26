package handler

import (
	"log"
	"net/http"

	"github.com/bizpulse/user-svc/internal/middleware"
	"github.com/bizpulse/user-svc/internal/model"
	"github.com/bizpulse/user-svc/internal/repository"
)

type BusinessHandler struct {
	bizRepo      *repository.BusinessRepo
	auditRepo    *repository.AuditRepo
	maxBodyBytes int64
}

func NewBusinessHandler(bizRepo *repository.BusinessRepo, auditRepo *repository.AuditRepo, maxBodyBytes int64) *BusinessHandler {
	return &BusinessHandler{
		bizRepo:      bizRepo,
		auditRepo:    auditRepo,
		maxBodyBytes: maxBodyBytes,
	}
}

// GetCurrent handles GET /v1/businesses/current.
// Returns the business associated with the authenticated user.
// Tenant isolation is enforced through the membership join.
func (h *BusinessHandler) GetCurrent(w http.ResponseWriter, r *http.Request) {
	userID, ok := middleware.GetUserID(r.Context())
	if !ok {
		writeError(w, http.StatusUnauthorized, "UNAUTHORIZED", "Authentication required")
		return
	}

	biz, err := h.bizRepo.FindByUserID(r.Context(), userID)
	if err != nil {
		log.Printf("ERROR: find business: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to fetch business")
		return
	}
	if biz == nil {
		writeError(w, http.StatusNotFound, "NOT_FOUND", "No business found for this user")
		return
	}

	writeJSON(w, http.StatusOK, model.BusinessResponse{
		ID:                      biz.ID,
		LegalName:               biz.LegalName,
		TradingName:             biz.TradingName,
		TaxIdentificationNumber: biz.TaxIdentificationNumber,
		IndustrySector:          biz.IndustrySector,
		BaseCurrency:            biz.BaseCurrency,
	})
}

// UpdateCurrent handles PATCH /v1/businesses/current.
// Partially updates the business associated with the authenticated user.
// Tenant isolation is enforced via membership check in the repository.
func (h *BusinessHandler) UpdateCurrent(w http.ResponseWriter, r *http.Request) {
	userID, ok := middleware.GetUserID(r.Context())
	if !ok {
		writeError(w, http.StatusUnauthorized, "UNAUTHORIZED", "Authentication required")
		return
	}

	r.Body = http.MaxBytesReader(w, r.Body, h.maxBodyBytes)

	var req model.UpdateBusinessRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Validate at least one field is provided
	if req.LegalName == nil && req.TradingName == nil && req.TIN == nil && req.Industry == nil {
		writeError(w, http.StatusBadRequest, "VALIDATION_ERROR", "At least one field must be provided")
		return
	}

	// First find the user's current business (tenant isolation)
	currentBiz, err := h.bizRepo.FindByUserID(r.Context(), userID)
	if err != nil {
		log.Printf("ERROR: find current business: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to update business")
		return
	}
	if currentBiz == nil {
		writeError(w, http.StatusNotFound, "NOT_FOUND", "No business found for this user")
		return
	}

	biz, err := h.bizRepo.Update(r.Context(), currentBiz.ID, userID, req)
	if err != nil {
		log.Printf("ERROR: update business: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to update business")
		return
	}
	if biz == nil {
		writeError(w, http.StatusNotFound, "NOT_FOUND", "Business not found or access denied")
		return
	}

	// Audit log (non-critical)
	if err := h.auditRepo.Log(r.Context(), &biz.ID, &userID, "business", biz.ID, "business.updated", biz); err != nil {
		log.Printf("WARN: audit log failed for business update: %v", err)
	}

	writeJSON(w, http.StatusOK, model.BusinessResponse{
		ID:                      biz.ID,
		LegalName:               biz.LegalName,
		TradingName:             biz.TradingName,
		TaxIdentificationNumber: biz.TaxIdentificationNumber,
		IndustrySector:          biz.IndustrySector,
		BaseCurrency:            biz.BaseCurrency,
	})
}
