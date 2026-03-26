"""API endpoint tests for BizPulse AI compliance-svc.

Tests use mocked database and auth to verify endpoint behavior
without requiring a running PostgreSQL instance.
"""

import json
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app
from auth import get_current_user

MOCK_USER = {
    "user_id": str(uuid4()),
    "business_id": str(uuid4()),
    "role": "owner",
}

MOCK_BUSINESS_ID = MOCK_USER["business_id"]


def mock_get_current_user():
    return MOCK_USER


# Override FastAPI dependency
app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)


def auth_headers():
    """Return headers (dependency override handles auth)."""
    return {}


# ============================================================
# Health endpoint
# ============================================================

class TestHealth:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "compliance-svc"


# ============================================================
# Tax periods
# ============================================================

class TestTaxPeriods:
    @patch("main.query")
    def test_list_periods(self, mock_query):
        mock_query.return_value = []
        response = client.get("/tax/periods", headers=auth_headers())
        assert response.status_code == 200
        assert response.json() == []

    def test_create_period_invalid_dates(self):
        response = client.post(
            "/tax/periods",
            json={
                "period_type": "VAT_MONTHLY",
                "start_date": "2026-03-31",
                "end_date": "2026-03-01",  # end before start
            },
            headers=auth_headers(),
        )
        assert response.status_code == 400

    def test_create_period_invalid_type(self):
        response = client.post(
            "/tax/periods",
            json={
                "period_type": "INVALID",
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
            },
            headers=auth_headers(),
        )
        assert response.status_code == 422  # Pydantic validation


# ============================================================
# Tax rates
# ============================================================

class TestTaxRates:
    @patch("main.query")
    def test_get_rates(self, mock_query):
        mock_query.return_value = [
            {
                "rate_type": "VAT",
                "rate_code": "VAT_STANDARD",
                "percentage_basis_points": 1500,
                "effective_from": date(2023, 1, 1),
                "effective_to": None,
                "source_reference": "GRA VAT Act",
            }
        ]
        response = client.get("/tax/rates", headers=auth_headers())
        assert response.status_code == 200


# ============================================================
# Tax metadata
# ============================================================

class TestTaxMetadata:
    def test_update_invalid_category(self):
        response = client.patch(
            f"/tax/metadata/{uuid4()}",
            json={"tax_category": "INVALID"},
            headers=auth_headers(),
        )
        assert response.status_code == 400

    @patch("main.query_single")
    @patch("main.execute_in_transaction")
    def test_update_valid_category(self, mock_execute, mock_single):
        txn_id = str(uuid4())
        mock_single.return_value = {"id": txn_id, "business_id": MOCK_BUSINESS_ID}
        mock_execute.return_value = None

        response = client.patch(
            f"/tax/metadata/{txn_id}",
            json={"tax_category": "EXEMPT"},
            headers=auth_headers(),
        )
        assert response.status_code == 200

    @patch("main.query_single")
    def test_update_nonexistent_transaction(self, mock_single):
        mock_single.return_value = None
        response = client.patch(
            f"/tax/metadata/{uuid4()}",
            json={"tax_category": "EXEMPT"},
            headers=auth_headers(),
        )
        assert response.status_code == 404


# ============================================================
# Compute endpoint validation
# ============================================================

class TestCompute:
    @patch("main.release_connection")
    @patch("main.get_connection")
    def test_compute_filed_period_rejected(self, mock_get_conn, mock_release):
        period_id = str(uuid4())
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": period_id,
            "business_id": MOCK_BUSINESS_ID,
            "period_type": "VAT_MONTHLY",
            "start_date": date(2026, 3, 1),
            "end_date": date(2026, 3, 31),
            "status": "FILED",
        }
        mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        response = client.post(
            f"/tax/periods/{period_id}/compute",
            headers=auth_headers(),
        )
        assert response.status_code in (400, 409)  # FILED period cannot be recomputed


# ============================================================
# Mark filed validation
# ============================================================

class TestMarkFiled:
    @patch("main.query_single")
    def test_mark_filed_draft_rejected(self, mock_single):
        period_id = str(uuid4())
        mock_single.return_value = {
            "id": period_id,
            "business_id": MOCK_BUSINESS_ID,
            "status": "DRAFT",
        }
        response = client.post(
            f"/tax/periods/{period_id}/mark-filed",
            json={"filing_reference": "GRA-2026-001"},
            headers=auth_headers(),
        )
        assert response.status_code == 400

    @patch("main.query_single")
    def test_mark_filed_not_found(self, mock_single):
        mock_single.return_value = None
        response = client.post(
            f"/tax/periods/{uuid4()}/mark-filed",
            json={"filing_reference": "GRA-2026-001"},
            headers=auth_headers(),
        )
        assert response.status_code == 404
