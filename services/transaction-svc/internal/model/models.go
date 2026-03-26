package model

import (
	"time"

	"github.com/google/uuid"
)

type User struct {
	ID                uuid.UUID `json:"id"`
	Email             string    `json:"email"`
	PasswordHash      string    `json:"-"`
	FirstName         string    `json:"first_name"`
	LastName          string    `json:"last_name"`
	PreferredLanguage string    `json:"preferred_language"`
	Status            string    `json:"status"`
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
}

type Business struct {
	ID                      uuid.UUID `json:"id"`
	LegalName               string    `json:"legal_name"`
	TradingName             *string   `json:"trading_name,omitempty"`
	RegistrationNumber      *string   `json:"registration_number,omitempty"`
	TaxIdentificationNumber *string   `json:"tax_identification_number,omitempty"`
	IndustrySector          *string   `json:"industry_sector,omitempty"`
	BaseCurrency            string    `json:"base_currency"`
	CountryCode             string    `json:"country_code"`
	Status                  string    `json:"status"`
	CreatedAt               time.Time `json:"created_at"`
	UpdatedAt               time.Time `json:"updated_at"`
}

type ConsentRecord struct {
	ID               uuid.UUID  `json:"id"`
	UserID           uuid.UUID  `json:"user_id"`
	BusinessID       *uuid.UUID `json:"business_id,omitempty"`
	ConsentCategory  string     `json:"consent_category"`
	Granted          bool       `json:"granted"`
	CapturedAt       time.Time  `json:"captured_at"`
	WithdrawnAt      *time.Time `json:"withdrawn_at,omitempty"`
	SourceChannel    string     `json:"source_channel"`
	PolicyVersion    string     `json:"policy_version"`
}

type Transaction struct {
	ID              uuid.UUID `json:"id"`
	BusinessID      uuid.UUID `json:"business_id"`
	IdempotencyKey  string    `json:"idempotency_key"`
	Type            string    `json:"type"`
	AmountPesewas   int64     `json:"amount_pesewas"`
	AccountCode     string    `json:"account_code"`
	Description     *string   `json:"description,omitempty"`
	TransactionDate time.Time `json:"transaction_date"`
	CreatedAt       time.Time `json:"created_at"`
	CreatedBy       uuid.UUID `json:"created_by"`
}

type AuditEntry struct {
	ID              uuid.UUID  `json:"id"`
	BusinessID      *uuid.UUID `json:"business_id,omitempty"`
	ActorUserID     *uuid.UUID `json:"actor_user_id,omitempty"`
	EntityType      string     `json:"entity_type"`
	EntityID        uuid.UUID  `json:"entity_id"`
	ActionCode      string     `json:"action_code"`
	BeforeSnapshot  []byte     `json:"before_snapshot,omitempty"`
	AfterSnapshot   []byte     `json:"after_snapshot,omitempty"`
	OccurredAt      time.Time  `json:"occurred_at"`
	IPAddressMasked *string    `json:"ip_address_masked,omitempty"`
}

type ChartOfAccount struct {
	ID              uuid.UUID  `json:"id"`
	BusinessID      *uuid.UUID `json:"business_id,omitempty"`
	AccountCode     string     `json:"account_code"`
	AccountName     string     `json:"account_name"`
	AccountType     string     `json:"account_type"`
	IsSystemDefault bool       `json:"is_system_default"`
	Active          bool       `json:"active"`
}

// API request/response types

type RegisterRequest struct {
	Email        string `json:"email"`
	Password     string `json:"password"`
	FirstName    string `json:"first_name"`
	LastName     string `json:"last_name"`
	BusinessName string `json:"business_name"`
}

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type AuthResponse struct {
	Token    string   `json:"token"`
	User     User     `json:"user"`
	Business Business `json:"business"`
}

type CreateTransactionRequest struct {
	IdempotencyKey  string  `json:"idempotency_key"`
	Type            string  `json:"type"`
	AmountPesewas   int64   `json:"amount_pesewas"`
	AccountCode     string  `json:"account_code"`
	Description     *string `json:"description,omitempty"`
	TransactionDate string  `json:"transaction_date"` // YYYY-MM-DD
}

type TransactionListResponse struct {
	Transactions []Transaction `json:"transactions"`
	Total        int           `json:"total"`
}

type ErrorResponse struct {
	Error ErrorDetail `json:"error"`
}

type ErrorDetail struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Details any    `json:"details,omitempty"`
}
