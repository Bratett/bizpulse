package repository

import (
	"context"
	"encoding/json"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
)

type AuditRepo struct {
	pool *pgxpool.Pool
}

func NewAuditRepo(pool *pgxpool.Pool) *AuditRepo {
	return &AuditRepo{pool: pool}
}

func (r *AuditRepo) Log(ctx context.Context, businessID *uuid.UUID, actorID *uuid.UUID, entityType string, entityID uuid.UUID, action string, after any) error {
	var afterJSON []byte
	if after != nil {
		var err error
		afterJSON, err = json.Marshal(after)
		if err != nil {
			return err
		}
	}

	_, err := r.pool.Exec(ctx,
		`INSERT INTO audit_log (business_id, actor_user_id, entity_type, entity_id, action_code, after_snapshot)
		 VALUES ($1, $2, $3, $4, $5, $6)`,
		businessID, actorID, entityType, entityID, action, afterJSON,
	)
	return err
}
