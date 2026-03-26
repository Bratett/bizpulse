"""
Lightweight Kafka/Redpanda producer for BizPulse AI compliance-svc.

Publishes tax-computation and tax-filing events so downstream consumers
(analytics-svc, notification-svc) can react asynchronously.

Graceful degradation: if confluent-kafka is not installed or Redpanda is
unreachable, events are logged and silently dropped -- the service keeps
working without Kafka.

Config:
    KAFKA_BOOTSTRAP_SERVERS  (default: redpanda:9092)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attempt to import confluent-kafka; fall back to no-op if unavailable
# ---------------------------------------------------------------------------

_producer = None
_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")

try:
    from confluent_kafka import Producer as _ConfluentProducer

    def _init_producer() -> _ConfluentProducer | None:
        """Lazily initialise the Kafka producer on first publish."""
        global _producer
        if _producer is not None:
            return _producer
        try:
            _producer = _ConfluentProducer({
                "bootstrap.servers": _BOOTSTRAP_SERVERS,
                "client.id": "compliance-svc",
                "acks": "all",
                "retries": 3,
                "retry.backoff.ms": 500,
            })
            logger.info("Kafka producer initialised (servers=%s)", _BOOTSTRAP_SERVERS)
            return _producer
        except Exception:
            logger.warning(
                "Failed to initialise Kafka producer — events will not be published",
                exc_info=True,
            )
            return None

except ImportError:
    logger.warning(
        "confluent-kafka is not installed — Kafka event publishing is disabled. "
        "Install with: pip install confluent-kafka"
    )

    def _init_producer():  # type: ignore[misc]
        return None


# ---------------------------------------------------------------------------
# Delivery callback
# ---------------------------------------------------------------------------

def _delivery_report(err, msg):
    """Called once per message to indicate delivery result."""
    if err is not None:
        logger.error("Kafka delivery failed for topic %s: %s", msg.topic(), err)
    else:
        logger.debug(
            "Kafka message delivered to %s [%d] @ %d",
            msg.topic(), msg.partition(), msg.offset(),
        )


# ---------------------------------------------------------------------------
# Internal publish helper
# ---------------------------------------------------------------------------

def _publish(topic: str, key: str, payload: dict) -> None:
    """Serialize *payload* as JSON and publish to *topic*.

    Non-blocking: errors are logged, never raised to callers.
    """
    producer = _init_producer()
    if producer is None:
        logger.debug("Kafka producer unavailable — dropping event on topic=%s key=%s", topic, key)
        return

    try:
        value = json.dumps(payload, default=str).encode("utf-8")
        producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=value,
            callback=_delivery_report,
        )
        # Trigger delivery callbacks (non-blocking poll)
        producer.poll(0)
    except Exception:
        logger.warning(
            "Failed to publish event to topic=%s key=%s",
            topic, key,
            exc_info=True,
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def publish_tax_computed(
    period_id: str,
    business_id: str,
    period_type: str,
    total_liability_pesewas: int,
    computed_at: datetime | None = None,
) -> None:
    """Publish a ``tax.computed`` event after a tax period is computed."""
    _publish(
        topic="compliance.tax.computed",
        key=period_id,
        payload={
            "event": "tax.computed",
            "period_id": period_id,
            "business_id": business_id,
            "period_type": period_type,
            "total_liability_pesewas": total_liability_pesewas,
            "computed_at": (computed_at or datetime.now(timezone.utc)).isoformat(),
        },
    )


def publish_tax_filed(
    period_id: str,
    business_id: str,
    filing_id: str,
    filing_reference: str | None = None,
    filed_at: datetime | None = None,
) -> None:
    """Publish a ``tax.filed`` event after a period is marked as filed."""
    _publish(
        topic="compliance.tax.filed",
        key=period_id,
        payload={
            "event": "tax.filed",
            "period_id": period_id,
            "business_id": business_id,
            "filing_id": filing_id,
            "filing_reference": filing_reference,
            "filed_at": (filed_at or datetime.now(timezone.utc)).isoformat(),
        },
    )
