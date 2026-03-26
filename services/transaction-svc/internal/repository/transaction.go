package repository

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/bizpulse/transaction-svc/internal/model"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"
)

var ErrDuplicateIdempotencyKey = errors.New("duplicate idempotency key")

type TransactionRepo struct {
	pool *pgxpool.Pool
}

func NewTransactionRepo(pool *pgxpool.Pool) *TransactionRepo {
	return &TransactionRepo{pool: pool}
}

// CreateWithAudit inserts a transaction and its audit log entry atomically.
// Both succeed or both fail — no partial writes for compliance.
func (r *TransactionRepo) CreateWithAudit(ctx context.Context, txn *model.Transaction) error {
	tx, err := r.pool.Begin(ctx)
	if err != nil {
		return fmt.Errorf("begin tx: %w", err)
	}
	defer tx.Rollback(ctx)

	// Insert transaction
	err = tx.QueryRow(ctx,
		`INSERT INTO transactions (business_id, idempotency_key, type, amount_pesewas, account_code, description, transaction_date, created_by)
		 VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		 RETURNING id, created_at`,
		txn.BusinessID, txn.IdempotencyKey, txn.Type, txn.AmountPesewas,
		txn.AccountCode, txn.Description, txn.TransactionDate, txn.CreatedBy,
	).Scan(&txn.ID, &txn.CreatedAt)

	if err != nil {
		if isDuplicateKeyError(err) {
			return ErrDuplicateIdempotencyKey
		}
		return fmt.Errorf("insert transaction: %w", err)
	}

	// Insert audit log in same transaction
	afterJSON, _ := json.Marshal(txn)
	_, err = tx.Exec(ctx,
		`INSERT INTO audit_log (business_id, actor_user_id, entity_type, entity_id, action_code, after_snapshot)
		 VALUES ($1, $2, $3, $4, $5, $6)`,
		txn.BusinessID, txn.CreatedBy, "transaction", txn.ID, "transaction.created", afterJSON,
	)
	if err != nil {
		return fmt.Errorf("insert audit log: %w", err)
	}

	if err := tx.Commit(ctx); err != nil {
		return fmt.Errorf("commit: %w", err)
	}

	return nil
}

func (r *TransactionRepo) List(ctx context.Context, businessID uuid.UUID, filters TransactionFilters) ([]model.Transaction, int, error) {
	query := `SELECT id, business_id, idempotency_key, type, amount_pesewas, account_code,
	                 description, transaction_date, created_at, created_by
	          FROM transactions
	          WHERE business_id = $1`
	countQuery := `SELECT COUNT(*) FROM transactions WHERE business_id = $1`
	args := []any{businessID}
	countArgs := []any{businessID}
	argIdx := 2

	if filters.Type != "" {
		query += fmt.Sprintf(" AND type = $%d", argIdx)
		countQuery += fmt.Sprintf(" AND type = $%d", argIdx)
		args = append(args, filters.Type)
		countArgs = append(countArgs, filters.Type)
		argIdx++
	}
	if !filters.DateFrom.IsZero() {
		query += fmt.Sprintf(" AND transaction_date >= $%d", argIdx)
		countQuery += fmt.Sprintf(" AND transaction_date >= $%d", argIdx)
		args = append(args, filters.DateFrom)
		countArgs = append(countArgs, filters.DateFrom)
		argIdx++
	}
	if !filters.DateTo.IsZero() {
		query += fmt.Sprintf(" AND transaction_date <= $%d", argIdx)
		countQuery += fmt.Sprintf(" AND transaction_date <= $%d", argIdx)
		args = append(args, filters.DateTo)
		countArgs = append(countArgs, filters.DateTo)
		argIdx++
	}
	if filters.AccountCode != "" {
		query += fmt.Sprintf(" AND account_code = $%d", argIdx)
		countQuery += fmt.Sprintf(" AND account_code = $%d", argIdx)
		args = append(args, filters.AccountCode)
		countArgs = append(countArgs, filters.AccountCode)
		argIdx++
	}

	// Get total count
	var total int
	if err := r.pool.QueryRow(ctx, countQuery, countArgs...).Scan(&total); err != nil {
		return nil, 0, fmt.Errorf("count transactions: %w", err)
	}

	query += " ORDER BY transaction_date DESC, created_at DESC"

	if filters.Limit > 0 {
		query += fmt.Sprintf(" LIMIT $%d", argIdx)
		args = append(args, filters.Limit)
		argIdx++
	}
	if filters.Offset > 0 && filters.Offset <= 100000 {
		query += fmt.Sprintf(" OFFSET $%d", argIdx)
		args = append(args, filters.Offset)
	}

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, 0, fmt.Errorf("query transactions: %w", err)
	}
	defer rows.Close()

	var txns []model.Transaction
	for rows.Next() {
		var t model.Transaction
		if err := rows.Scan(&t.ID, &t.BusinessID, &t.IdempotencyKey, &t.Type,
			&t.AmountPesewas, &t.AccountCode, &t.Description,
			&t.TransactionDate, &t.CreatedAt, &t.CreatedBy); err != nil {
			return nil, 0, fmt.Errorf("scan transaction: %w", err)
		}
		txns = append(txns, t)
	}
	return txns, total, nil
}

func (r *TransactionRepo) ListAccounts(ctx context.Context, businessID uuid.UUID) ([]model.ChartOfAccount, error) {
	rows, err := r.pool.Query(ctx,
		`SELECT id, business_id, account_code, account_name, account_type, is_system_default, active
		 FROM chart_of_accounts
		 WHERE (business_id = $1 OR business_id IS NULL) AND active = TRUE
		 ORDER BY account_code`,
		businessID,
	)
	if err != nil {
		return nil, fmt.Errorf("query accounts: %w", err)
	}
	defer rows.Close()

	var accounts []model.ChartOfAccount
	for rows.Next() {
		var a model.ChartOfAccount
		if err := rows.Scan(&a.ID, &a.BusinessID, &a.AccountCode, &a.AccountName,
			&a.AccountType, &a.IsSystemDefault, &a.Active); err != nil {
			return nil, fmt.Errorf("scan account: %w", err)
		}
		accounts = append(accounts, a)
	}
	return accounts, nil
}

func (r *TransactionRepo) ValidateAccountCode(ctx context.Context, businessID uuid.UUID, accountCode string) (bool, error) {
	var exists bool
	err := r.pool.QueryRow(ctx,
		`SELECT EXISTS(
			SELECT 1 FROM chart_of_accounts
			WHERE (business_id = $1 OR business_id IS NULL)
			AND account_code = $2
			AND active = TRUE
		)`,
		businessID, accountCode,
	).Scan(&exists)
	if err != nil && !errors.Is(err, pgx.ErrNoRows) {
		return false, err
	}
	return exists, nil
}

type TransactionFilters struct {
	Type        string
	DateFrom    time.Time
	DateTo      time.Time
	AccountCode string
	Limit       int
	Offset      int
}

func isDuplicateKeyError(err error) bool {
	var pgErr *pgconn.PgError
	if errors.As(err, &pgErr) {
		return pgErr.Code == "23505" // unique_violation
	}
	return false
}
