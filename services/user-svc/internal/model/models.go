package model

import (
	"time"

	"github.com/google/uuid"
)

// Domain models — match the DB schema from migration 000001

type User struct {
	ID                uuid.UUID `json:"id"`
	Email             string    `json:"email"`
	KeycloakID        string    `json:"-"` // Keycloak sub, never exposed
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

// API request/response types

type RegisterRequest struct {
	Email        string `json:"email"`
	Password     string `json:"password"`
	FirstName    string `json:"first_name"`
	LastName     string `json:"last_name"`
	BusinessName string `json:"business_name"`
	Industry     string `json:"industry,omitempty"`
}

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type AuthResponse struct {
	AccessToken  string   `json:"access_token"`
	RefreshToken string   `json:"refresh_token,omitempty"`
	TokenType    string   `json:"token_type"`
	ExpiresIn    int      `json:"expires_in"`
	User         User     `json:"user"`
	Business     Business `json:"business"`
}

type UserResponse struct {
	ID                uuid.UUID `json:"id"`
	Email             string    `json:"email"`
	FirstName         string    `json:"first_name"`
	LastName          string    `json:"last_name"`
	PreferredLanguage string    `json:"preferred_language"`
	Status            string    `json:"status"`
}

type BusinessResponse struct {
	ID                      uuid.UUID `json:"id"`
	LegalName               string    `json:"legal_name"`
	TradingName             *string   `json:"trading_name,omitempty"`
	TaxIdentificationNumber *string   `json:"tax_identification_number,omitempty"`
	IndustrySector          *string   `json:"industry_sector,omitempty"`
	BaseCurrency            string    `json:"base_currency"`
}

type UpdateUserRequest struct {
	FirstName         *string `json:"first_name,omitempty"`
	LastName          *string `json:"last_name,omitempty"`
	PreferredLanguage *string `json:"preferred_language,omitempty"`
}

type UpdateBusinessRequest struct {
	LegalName   *string `json:"legal_name,omitempty"`
	TradingName *string `json:"trading_name,omitempty"`
	TIN         *string `json:"tin,omitempty"`
	Industry    *string `json:"industry_sector,omitempty"`
}

// Shared error envelope (matches API_CONTRACT.md section 5.3)

type ErrorResponse struct {
	Error ErrorDetail `json:"error"`
}

type ErrorDetail struct {
	Code    string `json:"code"`
	Message string `json:"message"`
	Details any    `json:"details,omitempty"`
}
