package repository

import (
	"context"
	"errors"
	"fmt"

	"github.com/bizpulse/user-svc/internal/model"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type BusinessRepo struct {
	pool *pgxpool.Pool
}

func NewBusinessRepo(pool *pgxpool.Pool) *BusinessRepo {
	return &BusinessRepo{pool: pool}
}

// FindByID fetches a business by ID. Caller must enforce tenant isolation
// by verifying the requesting user has a membership for this business.
func (r *BusinessRepo) FindByID(ctx context.Context, businessID uuid.UUID) (*model.Business, error) {
	var biz model.Business
	err := r.pool.QueryRow(ctx,
		`SELECT id, legal_name, trading_name, registration_number, tax_identification_number,
		        industry_sector, base_currency, country_code, status, created_at, updated_at
		 FROM businesses
		 WHERE id = $1 AND status = 'active'`,
		businessID,
	).Scan(&biz.ID, &biz.LegalName, &biz.TradingName, &biz.RegistrationNumber,
		&biz.TaxIdentificationNumber, &biz.IndustrySector, &biz.BaseCurrency,
		&biz.CountryCode, &biz.Status, &biz.CreatedAt, &biz.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}
		return nil, fmt.Errorf("find business: %w", err)
	}
	return &biz, nil
}

// FindByUserID fetches the business associated with a user through the membership table.
// This enforces tenant isolation — users can only access businesses they belong to.
func (r *BusinessRepo) FindByUserID(ctx context.Context, userID uuid.UUID) (*model.Business, error) {
	var biz model.Business
	err := r.pool.QueryRow(ctx,
		`SELECT b.id, b.legal_name, b.trading_name, b.registration_number,
		        b.tax_identification_number, b.industry_sector, b.base_currency,
		        b.country_code, b.status, b.created_at, b.updated_at
		 FROM businesses b
		 JOIN user_business_memberships m ON m.business_id = b.id
		 WHERE m.user_id = $1 AND b.status = 'active'
		 LIMIT 1`,
		userID,
	).Scan(&biz.ID, &biz.LegalName, &biz.TradingName, &biz.RegistrationNumber,
		&biz.TaxIdentificationNumber, &biz.IndustrySector, &biz.BaseCurrency,
		&biz.CountryCode, &biz.Status, &biz.CreatedAt, &biz.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}
		return nil, fmt.Errorf("find business by user: %w", err)
	}
	return &biz, nil
}

// Update partially updates business fields. Only non-nil fields in the request are applied.
// Scoped by business_id AND verified through user membership for tenant isolation.
func (r *BusinessRepo) Update(ctx context.Context, businessID uuid.UUID, userID uuid.UUID, req model.UpdateBusinessRequest) (*model.Business, error) {
	// Verify user has membership for this business (tenant isolation)
	var membershipExists bool
	err := r.pool.QueryRow(ctx,
		`SELECT EXISTS(
			SELECT 1 FROM user_business_memberships
			WHERE user_id = $1 AND business_id = $2
		)`,
		userID, businessID,
	).Scan(&membershipExists)
	if err != nil {
		return nil, fmt.Errorf("check membership: %w", err)
	}
	if !membershipExists {
		return nil, nil // unauthorized — no membership
	}

	var biz model.Business
	err = r.pool.QueryRow(ctx,
		`UPDATE businesses SET
			legal_name               = COALESCE($2, legal_name),
			trading_name             = COALESCE($3, trading_name),
			tax_identification_number = COALESCE($4, tax_identification_number),
			industry_sector          = COALESCE($5, industry_sector),
			updated_at               = NOW()
		 WHERE id = $1 AND status = 'active'
		 RETURNING id, legal_name, trading_name, registration_number, tax_identification_number,
		           industry_sector, base_currency, country_code, status, created_at, updated_at`,
		businessID, req.LegalName, req.TradingName, req.TIN, req.Industry,
	).Scan(&biz.ID, &biz.LegalName, &biz.TradingName, &biz.RegistrationNumber,
		&biz.TaxIdentificationNumber, &biz.IndustrySector, &biz.BaseCurrency,
		&biz.CountryCode, &biz.Status, &biz.CreatedAt, &biz.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}
		return nil, fmt.Errorf("update business: %w", err)
	}
	return &biz, nil
}
