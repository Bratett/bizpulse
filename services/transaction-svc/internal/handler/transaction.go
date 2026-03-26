package handler

import (
	"context"
	"errors"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/bizpulse/transaction-svc/internal/middleware"
	"github.com/bizpulse/transaction-svc/internal/model"
	"github.com/bizpulse/transaction-svc/internal/repository"
	"github.com/google/uuid"
)

type TransactionHandler struct {
	txnRepo      *repository.TransactionRepo
	maxBodyBytes int64
}

func NewTransactionHandler(txnRepo *repository.TransactionRepo, maxBodyBytes int64) *TransactionHandler {
	return &TransactionHandler{txnRepo: txnRepo, maxBodyBytes: maxBodyBytes}
}

func (h *TransactionHandler) Create(w http.ResponseWriter, r *http.Request) {
	claims := middleware.GetClaims(r.Context())
	if claims == nil {
		writeError(w, http.StatusUnauthorized, "UNAUTHORIZED", "Authentication required")
		return
	}

	userID, err := uuid.Parse(claims.Subject)
	if err != nil {
		writeError(w, http.StatusUnauthorized, "UNAUTHORIZED", "Invalid token")
		return
	}

	// Limit request body size
	r.Body = http.MaxBytesReader(w, r.Body, h.maxBodyBytes)

	var req model.CreateTransactionRequest
	if err := decodeJSON(r, &req); err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	if req.IdempotencyKey == "" {
		req.IdempotencyKey = r.Header.Get("X-Idempotency-Key")
	}

	if errs := validateTransactionRequest(req); len(errs) > 0 {
		writeErrorWithDetails(w, http.StatusBadRequest, "VALIDATION_ERROR", "Validation failed", errs)
		return
	}

	// Validate account code exists
	valid, err := h.txnRepo.ValidateAccountCode(r.Context(), claims.BusinessID, req.AccountCode)
	if err != nil {
		log.Printf("ERROR: validate account: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to validate account code")
		return
	}
	if !valid {
		writeError(w, http.StatusBadRequest, "INVALID_ACCOUNT", "Account code does not exist")
		return
	}

	txnDate, err := time.Parse("2006-01-02", req.TransactionDate)
	if err != nil {
		writeError(w, http.StatusBadRequest, "VALIDATION_ERROR", "Invalid date format. Use YYYY-MM-DD")
		return
	}

	txn := &model.Transaction{
		BusinessID:      claims.BusinessID,
		IdempotencyKey:  req.IdempotencyKey,
		Type:            strings.ToUpper(req.Type),
		AmountPesewas:   req.AmountPesewas,
		AccountCode:     req.AccountCode,
		Description:     req.Description,
		TransactionDate: txnDate,
		CreatedBy:       userID,
	}

	// Atomic: transaction + audit log in single DB transaction
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	if err := h.txnRepo.CreateWithAudit(ctx, txn); err != nil {
		if errors.Is(err, repository.ErrDuplicateIdempotencyKey) {
			writeError(w, http.StatusConflict, "DUPLICATE_TRANSACTION", "A transaction with this idempotency key already exists")
			return
		}
		log.Printf("ERROR: create transaction: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to create transaction")
		return
	}

	writeJSON(w, http.StatusCreated, txn)
}

func (h *TransactionHandler) List(w http.ResponseWriter, r *http.Request) {
	claims := middleware.GetClaims(r.Context())
	if claims == nil {
		writeError(w, http.StatusUnauthorized, "UNAUTHORIZED", "Authentication required")
		return
	}

	q := r.URL.Query()

	// Validate type filter
	txnType := strings.ToUpper(q.Get("type"))
	if txnType != "" && txnType != "INCOME" && txnType != "EXPENSE" {
		writeError(w, http.StatusBadRequest, "VALIDATION_ERROR", "Type must be INCOME or EXPENSE")
		return
	}

	filters := repository.TransactionFilters{
		Type:        txnType,
		AccountCode: q.Get("account_code"),
		Limit:       50,
	}

	if v := q.Get("date_from"); v != "" {
		if t, err := time.Parse("2006-01-02", v); err == nil {
			filters.DateFrom = t
		}
	}
	if v := q.Get("date_to"); v != "" {
		if t, err := time.Parse("2006-01-02", v); err == nil {
			filters.DateTo = t
		}
	}
	if v := q.Get("limit"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 && n <= 200 {
			filters.Limit = n
		}
	}
	if v := q.Get("offset"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n >= 0 {
			filters.Offset = n
		}
	}

	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	txns, total, err := h.txnRepo.List(ctx, claims.BusinessID, filters)
	if err != nil {
		log.Printf("ERROR: list transactions: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to list transactions")
		return
	}

	if txns == nil {
		txns = []model.Transaction{}
	}

	writeJSON(w, http.StatusOK, model.TransactionListResponse{
		Transactions: txns,
		Total:        total,
	})
}

func (h *TransactionHandler) ListAccounts(w http.ResponseWriter, r *http.Request) {
	claims := middleware.GetClaims(r.Context())
	if claims == nil {
		writeError(w, http.StatusUnauthorized, "UNAUTHORIZED", "Authentication required")
		return
	}

	accounts, err := h.txnRepo.ListAccounts(r.Context(), claims.BusinessID)
	if err != nil {
		log.Printf("ERROR: list accounts: %v", err)
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to list accounts")
		return
	}

	if accounts == nil {
		accounts = []model.ChartOfAccount{}
	}

	writeJSON(w, http.StatusOK, accounts)
}

func validateTransactionRequest(req model.CreateTransactionRequest) map[string]string {
	errs := make(map[string]string)

	if req.IdempotencyKey == "" {
		errs["idempotency_key"] = "Idempotency key is required"
	}

	txnType := strings.ToUpper(req.Type)
	if txnType != "INCOME" && txnType != "EXPENSE" {
		errs["type"] = "Type must be INCOME or EXPENSE"
	}

	if req.AmountPesewas <= 0 {
		errs["amount_pesewas"] = "Amount must be a positive integer (in pesewas)"
	} else if req.AmountPesewas > 10_000_000_000 {
		errs["amount_pesewas"] = "Amount exceeds maximum allowed value"
	}

	if req.AccountCode == "" {
		errs["account_code"] = "Account code is required"
	}

	if req.TransactionDate == "" {
		errs["transaction_date"] = "Transaction date is required (YYYY-MM-DD)"
	} else if _, err := time.Parse("2006-01-02", req.TransactionDate); err != nil {
		errs["transaction_date"] = "Invalid date format. Use YYYY-MM-DD"
	}

	return errs
}
