package repository

import (
	"context"
	"errors"
	"fmt"

	"github.com/bizpulse/transaction-svc/internal/model"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

var ErrEmailExists = errors.New("email already registered")

type UserRepo struct {
	pool *pgxpool.Pool
}

func NewUserRepo(pool *pgxpool.Pool) *UserRepo {
	return &UserRepo{pool: pool}
}

// Register creates a user, business, membership, and consent record in a single transaction.
func (r *UserRepo) Register(ctx context.Context, req model.RegisterRequest, passwordHash string) (*model.User, *model.Business, error) {
	tx, err := r.pool.Begin(ctx)
	if err != nil {
		return nil, nil, fmt.Errorf("begin tx: %w", err)
	}
	defer tx.Rollback(ctx)

	// Check email uniqueness
	var exists bool
	err = tx.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)", req.Email).Scan(&exists)
	if err != nil {
		return nil, nil, fmt.Errorf("check email: %w", err)
	}
	if exists {
		return nil, nil, ErrEmailExists
	}

	// Create user
	var user model.User
	err = tx.QueryRow(ctx,
		`INSERT INTO users (email, password_hash, first_name, last_name)
		 VALUES ($1, $2, $3, $4)
		 RETURNING id, email, first_name, last_name, preferred_language, status, created_at, updated_at`,
		req.Email, passwordHash, req.FirstName, req.LastName,
	).Scan(&user.ID, &user.Email, &user.FirstName, &user.LastName,
		&user.PreferredLanguage, &user.Status, &user.CreatedAt, &user.UpdatedAt)
	if err != nil {
		return nil, nil, fmt.Errorf("insert user: %w", err)
	}

	// Create business
	var biz model.Business
	err = tx.QueryRow(ctx,
		`INSERT INTO businesses (legal_name)
		 VALUES ($1)
		 RETURNING id, legal_name, trading_name, registration_number, tax_identification_number,
		           industry_sector, base_currency, country_code, status, created_at, updated_at`,
		req.BusinessName,
	).Scan(&biz.ID, &biz.LegalName, &biz.TradingName, &biz.RegistrationNumber,
		&biz.TaxIdentificationNumber, &biz.IndustrySector, &biz.BaseCurrency,
		&biz.CountryCode, &biz.Status, &biz.CreatedAt, &biz.UpdatedAt)
	if err != nil {
		return nil, nil, fmt.Errorf("insert business: %w", err)
	}

	// Create membership (owner role)
	_, err = tx.Exec(ctx,
		`INSERT INTO user_business_memberships (user_id, business_id, role)
		 VALUES ($1, $2, 'owner')`,
		user.ID, biz.ID,
	)
	if err != nil {
		return nil, nil, fmt.Errorf("insert membership: %w", err)
	}

	// Create consent record (Ghana DPA 843 — CM-004)
	_, err = tx.Exec(ctx,
		`INSERT INTO consent_records (user_id, business_id, consent_category, granted, source_channel, policy_version)
		 VALUES ($1, $2, 'data_processing', TRUE, 'web', '1.0')`,
		user.ID, biz.ID,
	)
	if err != nil {
		return nil, nil, fmt.Errorf("insert consent: %w", err)
	}

	if err := tx.Commit(ctx); err != nil {
		return nil, nil, fmt.Errorf("commit: %w", err)
	}

	return &user, &biz, nil
}

func (r *UserRepo) FindByEmail(ctx context.Context, email string) (*model.User, error) {
	var user model.User
	err := r.pool.QueryRow(ctx,
		`SELECT id, email, password_hash, first_name, last_name, preferred_language, status, created_at, updated_at
		 FROM users WHERE email = $1 AND status = 'active'`,
		email,
	).Scan(&user.ID, &user.Email, &user.PasswordHash, &user.FirstName, &user.LastName,
		&user.PreferredLanguage, &user.Status, &user.CreatedAt, &user.UpdatedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil
		}
		return nil, fmt.Errorf("find user: %w", err)
	}
	return &user, nil
}

func (r *UserRepo) GetBusinessForUser(ctx context.Context, userID uuid.UUID) (*model.Business, string, error) {
	var biz model.Business
	var role string
	err := r.pool.QueryRow(ctx,
		`SELECT b.id, b.legal_name, b.trading_name, b.registration_number,
		        b.tax_identification_number, b.industry_sector, b.base_currency,
		        b.country_code, b.status, b.created_at, b.updated_at, m.role
		 FROM businesses b
		 JOIN user_business_memberships m ON m.business_id = b.id
		 WHERE m.user_id = $1
		 LIMIT 1`,
		userID,
	).Scan(&biz.ID, &biz.LegalName, &biz.TradingName, &biz.RegistrationNumber,
		&biz.TaxIdentificationNumber, &biz.IndustrySector, &biz.BaseCurrency,
		&biz.CountryCode, &biz.Status, &biz.CreatedAt, &biz.UpdatedAt, &role)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, "", nil
		}
		return nil, "", fmt.Errorf("get business: %w", err)
	}
	return &biz, role, nil
}
