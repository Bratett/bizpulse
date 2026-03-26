// Package kafka provides a Kafka/Redpanda event producer for transaction-svc.
//
// This module defines the Producer interface and ships with a no-op
// implementation so the service compiles and runs without any Kafka
// client dependency. When the Go module is updated with franz-go (or
// another client), a real implementation can be wired in via the
// NewProducer constructor.
//
// Environment:
//
//	KAFKA_BOOTSTRAP_SERVERS — comma-separated broker list (default: redpanda:9092)
package kafka

import (
	"encoding/json"
	"log"
	"os"
	"time"
)

// TransactionCreatedEvent is the payload published when a new transaction
// is persisted.  Field names follow the Avro schema contract in
// shared/avro/TransactionCreated.avsc.
type TransactionCreatedEvent struct {
	EventType       string `json:"event_type"`
	TransactionID   string `json:"transaction_id"`
	BusinessID      string `json:"business_id"`
	Type            string `json:"type"` // INCOME | EXPENSE
	AmountPesewas   int64  `json:"amount_pesewas"`
	AccountCode     string `json:"account_code"`
	TransactionDate string `json:"transaction_date"` // ISO-8601
	CreatedAt       string `json:"created_at"`       // ISO-8601
}

// Producer is the interface that concrete Kafka implementations must satisfy.
type Producer interface {
	// PublishTransactionCreated publishes a TransactionCreated event.
	// Implementations must be safe for concurrent use.
	PublishTransactionCreated(evt TransactionCreatedEvent) error

	// Close flushes pending messages and releases resources.
	Close() error
}

// ---------------------------------------------------------------------------
// No-op implementation (default when Kafka client is not wired in)
// ---------------------------------------------------------------------------

// NoopProducer silently discards all events.  It is used as a safe default
// when the real Kafka client has not been integrated yet.
type NoopProducer struct{}

// PublishTransactionCreated logs the event at debug level and returns nil.
func (n *NoopProducer) PublishTransactionCreated(evt TransactionCreatedEvent) error {
	data, _ := json.Marshal(evt)
	log.Printf("[kafka/noop] would publish TransactionCreated: %s", string(data))
	return nil
}

// Close is a no-op.
func (n *NoopProducer) Close() error {
	return nil
}

// ---------------------------------------------------------------------------
// Constructor
// ---------------------------------------------------------------------------

// BootstrapServers returns the configured broker list.
func BootstrapServers() string {
	if v := os.Getenv("KAFKA_BOOTSTRAP_SERVERS"); v != "" {
		return v
	}
	return "redpanda:9092"
}

// NewProducer returns a Producer implementation.  For now this always
// returns the NoopProducer.  When franz-go is added to go.mod, this
// function should be updated to return a real producer that connects to
// BootstrapServers().
func NewProducer() Producer {
	log.Printf("[kafka] producer initialised (noop) — brokers=%s", BootstrapServers())
	return &NoopProducer{}
}

// NewTransactionCreatedEvent is a convenience constructor.
func NewTransactionCreatedEvent(
	transactionID, businessID, txnType, accountCode, txnDate string,
	amountPesewas int64,
) TransactionCreatedEvent {
	return TransactionCreatedEvent{
		EventType:       "transaction.created",
		TransactionID:   transactionID,
		BusinessID:      businessID,
		Type:            txnType,
		AmountPesewas:   amountPesewas,
		AccountCode:     accountCode,
		TransactionDate: txnDate,
		CreatedAt:       time.Now().UTC().Format(time.RFC3339),
	}
}
