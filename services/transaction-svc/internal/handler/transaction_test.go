package handler

import (
	"testing"

	"github.com/bizpulse/transaction-svc/internal/model"
)

func TestValidateTransactionRequest(t *testing.T) {
	desc := "Office supplies"
	validReq := model.CreateTransactionRequest{
		IdempotencyKey:  "txn-001-abc",
		Type:            "INCOME",
		AmountPesewas:   500000, // 5000.00 GHS
		AccountCode:     "4000",
		Description:     &desc,
		TransactionDate: "2025-03-15",
	}

	t.Run("valid INCOME request", func(t *testing.T) {
		errs := validateTransactionRequest(validReq)
		if len(errs) != 0 {
			t.Errorf("expected no errors, got %v", errs)
		}
	})

	t.Run("valid EXPENSE request", func(t *testing.T) {
		req := validReq
		req.Type = "EXPENSE"
		errs := validateTransactionRequest(req)
		if len(errs) != 0 {
			t.Errorf("expected no errors, got %v", errs)
		}
	})

	t.Run("lowercase income is accepted", func(t *testing.T) {
		req := validReq
		req.Type = "income"
		errs := validateTransactionRequest(req)
		if _, ok := errs["type"]; ok {
			t.Error("lowercase 'income' should be accepted (function uppercases)")
		}
	})

	t.Run("lowercase expense is accepted", func(t *testing.T) {
		req := validReq
		req.Type = "expense"
		errs := validateTransactionRequest(req)
		if _, ok := errs["type"]; ok {
			t.Error("lowercase 'expense' should be accepted (function uppercases)")
		}
	})

	t.Run("missing idempotency_key", func(t *testing.T) {
		req := validReq
		req.IdempotencyKey = ""
		errs := validateTransactionRequest(req)
		if _, ok := errs["idempotency_key"]; !ok {
			t.Error("expected idempotency_key error, got none")
		}
	})

	t.Run("invalid type", func(t *testing.T) {
		tests := []struct {
			name    string
			txnType string
		}{
			{"empty type", ""},
			{"TRANSFER type", "TRANSFER"},
			{"REFUND type", "REFUND"},
			{"random string", "xyz"},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				req := validReq
				req.Type = tt.txnType
				errs := validateTransactionRequest(req)
				if _, ok := errs["type"]; !ok {
					t.Errorf("expected type error for %q, got none", tt.txnType)
				}
			})
		}
	})

	t.Run("amount zero", func(t *testing.T) {
		req := validReq
		req.AmountPesewas = 0
		errs := validateTransactionRequest(req)
		if _, ok := errs["amount_pesewas"]; !ok {
			t.Error("expected amount_pesewas error for zero, got none")
		}
	})

	t.Run("amount negative", func(t *testing.T) {
		req := validReq
		req.AmountPesewas = -100
		errs := validateTransactionRequest(req)
		if _, ok := errs["amount_pesewas"]; !ok {
			t.Error("expected amount_pesewas error for negative, got none")
		}
	})

	t.Run("amount exactly 1 pesewa is valid", func(t *testing.T) {
		req := validReq
		req.AmountPesewas = 1
		errs := validateTransactionRequest(req)
		if _, ok := errs["amount_pesewas"]; ok {
			t.Error("amount of 1 pesewa should be valid")
		}
	})

	t.Run("amount exactly at maximum is valid", func(t *testing.T) {
		req := validReq
		req.AmountPesewas = 10_000_000_000
		errs := validateTransactionRequest(req)
		if _, ok := errs["amount_pesewas"]; ok {
			t.Error("amount at 10_000_000_000 should be valid")
		}
	})

	t.Run("amount exceeds maximum", func(t *testing.T) {
		req := validReq
		req.AmountPesewas = 10_000_000_001
		errs := validateTransactionRequest(req)
		if _, ok := errs["amount_pesewas"]; !ok {
			t.Error("expected amount_pesewas error for exceeding max, got none")
		}
	})

	t.Run("amount far exceeds maximum", func(t *testing.T) {
		req := validReq
		req.AmountPesewas = 100_000_000_000
		errs := validateTransactionRequest(req)
		if _, ok := errs["amount_pesewas"]; !ok {
			t.Error("expected amount_pesewas error for far exceeding max, got none")
		}
	})

	t.Run("missing account_code", func(t *testing.T) {
		req := validReq
		req.AccountCode = ""
		errs := validateTransactionRequest(req)
		if _, ok := errs["account_code"]; !ok {
			t.Error("expected account_code error, got none")
		}
	})

	t.Run("missing transaction_date", func(t *testing.T) {
		req := validReq
		req.TransactionDate = ""
		errs := validateTransactionRequest(req)
		if _, ok := errs["transaction_date"]; !ok {
			t.Error("expected transaction_date error, got none")
		}
	})

	t.Run("invalid date format", func(t *testing.T) {
		tests := []struct {
			name string
			date string
		}{
			{"US format MM/DD/YYYY", "03/15/2025"},
			{"EU format DD-MM-YYYY", "15-03-2025"},
			{"ISO datetime", "2025-03-15T10:00:00Z"},
			{"partial date", "2025-03"},
			{"garbage", "not-a-date"},
			{"reversed", "15-2025-03"},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				req := validReq
				req.TransactionDate = tt.date
				errs := validateTransactionRequest(req)
				if _, ok := errs["transaction_date"]; !ok {
					t.Errorf("expected transaction_date error for %q, got none", tt.date)
				}
			})
		}
	})

	t.Run("valid date formats", func(t *testing.T) {
		tests := []struct {
			name string
			date string
		}{
			{"standard date", "2025-03-15"},
			{"beginning of year", "2025-01-01"},
			{"end of year", "2025-12-31"},
			{"leap day", "2024-02-29"},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				req := validReq
				req.TransactionDate = tt.date
				errs := validateTransactionRequest(req)
				if _, ok := errs["transaction_date"]; ok {
					t.Errorf("date %q should be valid", tt.date)
				}
			})
		}
	})

	t.Run("nil description is valid", func(t *testing.T) {
		req := validReq
		req.Description = nil
		errs := validateTransactionRequest(req)
		if len(errs) != 0 {
			t.Errorf("expected no errors with nil description, got %v", errs)
		}
	})

	t.Run("multiple errors at once", func(t *testing.T) {
		req := model.CreateTransactionRequest{}
		errs := validateTransactionRequest(req)

		expectedFields := []string{"idempotency_key", "type", "amount_pesewas", "account_code", "transaction_date"}
		for _, field := range expectedFields {
			if _, ok := errs[field]; !ok {
				t.Errorf("expected error for %q, got none", field)
			}
		}
		if len(errs) != len(expectedFields) {
			t.Errorf("expected %d errors, got %d: %v", len(expectedFields), len(errs), errs)
		}
	})
}
