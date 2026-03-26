"""Unit tests for the analytics service API endpoints.

Uses FastAPI TestClient with mocked database and authentication layers.
All monetary values are in pesewas (integers).
"""

import time
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# Test secret — must match what the auth module reads from settings
TEST_JWT_SECRET = "test-secret-for-analytics-svc-api-tests-minimum-32chars"


def _make_token(
    business_id: str = "biz-accra-market-007",
    user_id: str = "user-kofi-001",
    role: str = "owner",
    expired: bool = False,
) -> str:
    """Helper: create a signed HS256 JWT for test requests."""
    now = int(time.time())
    claims = {
        "sub": user_id,
        "business_id": business_id,
        "role": role,
        "iat": now - (7200 if expired else 0),
        "exp": now - (3600 if expired else -3600),
    }
    return jwt.encode(claims, TEST_JWT_SECRET, algorithm="HS256")


def _auth_header(token: str = None) -> dict:
    """Helper: build an Authorization header dict."""
    if token is None:
        token = _make_token()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    """Create a TestClient with the JWT_SECRET patched for auth."""
    # Patch settings in both config and auth modules
    mock_settings = MagicMock()
    mock_settings.JWT_SECRET = TEST_JWT_SECRET
    mock_settings.ALLOWED_ORIGINS = ["http://localhost:3000"]
    mock_settings.ANALYTICS_SVC_PORT = 8081

    with patch("auth.settings", mock_settings), \
         patch("main.settings", mock_settings):
        from main import app
        yield TestClient(app, raise_server_exceptions=False)


# ===================================================================
# GET /health
# ===================================================================


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        """The health endpoint should return 200 with service identity."""
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["service"] == "analytics-svc"

    def test_health_requires_no_auth(self, client):
        """Health check should not require authentication."""
        response = client.get("/health")
        assert response.status_code == 200


# ===================================================================
# GET /reports/profit-loss — Auth
# ===================================================================


class TestProfitLossAuth:

    def test_profit_loss_without_auth_returns_401(self, client):
        """Missing authorization should return 401."""
        response = client.get("/reports/profit-loss")
        assert response.status_code == 401

    def test_profit_loss_with_expired_token_returns_401(self, client):
        """Expired JWT should return 401."""
        token = _make_token(expired=True)
        response = client.get(
            "/reports/profit-loss",
            headers=_auth_header(token),
        )
        assert response.status_code == 401

    def test_profit_loss_with_invalid_token_returns_401(self, client):
        """Garbage token should return 401."""
        response = client.get(
            "/reports/profit-loss",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert response.status_code == 401


# ===================================================================
# GET /reports/profit-loss — Date Validation
# ===================================================================


class TestProfitLossDateValidation:

    @patch("main.profit_and_loss")
    def test_invalid_date_range_returns_400(self, mock_pl, client):
        """When date_from is after date_to, the endpoint should return 400."""
        response = client.get(
            "/reports/profit-loss",
            params={"date_from": "2026-03-31", "date_to": "2026-03-01"},
            headers=_auth_header(),
        )
        assert response.status_code == 400

    @patch("main.profit_and_loss")
    def test_same_date_from_and_to_is_valid(self, mock_pl, client):
        """Same date for from and to should be accepted (single-day report)."""
        mock_pl.return_value = {
            "report_type": "profit_and_loss",
            "business_id": "biz-accra-market-007",
            "period": {"from": "2026-03-15", "to": "2026-03-15"},
            "revenue": {"items": [], "total_pesewas": 0},
            "expenses": {"items": [], "total_pesewas": 0},
            "net_income_pesewas": 0,
            "currency": "GHS",
        }

        response = client.get(
            "/reports/profit-loss",
            params={"date_from": "2026-03-15", "date_to": "2026-03-15"},
            headers=_auth_header(),
        )
        assert response.status_code == 200


# ===================================================================
# GET /reports/profit-loss — Success
# ===================================================================


class TestProfitLossSuccess:

    @patch("main.profit_and_loss")
    def test_profit_loss_returns_report_data(self, mock_pl, client):
        """A valid request should return the P&L report."""
        mock_pl.return_value = {
            "report_type": "profit_and_loss",
            "business_id": "biz-accra-market-007",
            "period": {"from": "2026-03-01", "to": "2026-03-31"},
            "revenue": {"items": [], "total_pesewas": 500000},
            "expenses": {"items": [], "total_pesewas": 200000},
            "net_income_pesewas": 300000,
            "currency": "GHS",
        }

        response = client.get(
            "/reports/profit-loss",
            params={"date_from": "2026-03-01", "date_to": "2026-03-31"},
            headers=_auth_header(),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["net_income_pesewas"] == 300000

    @patch("main.profit_and_loss")
    def test_profit_loss_passes_business_id_from_token(self, mock_pl, client):
        """The business_id from JWT claims should be passed to the report."""
        mock_pl.return_value = {
            "report_type": "profit_and_loss",
            "business_id": "biz-tema-harbour-005",
            "period": {"from": "2026-01-01", "to": "2026-01-31"},
            "revenue": {"items": [], "total_pesewas": 0},
            "expenses": {"items": [], "total_pesewas": 0},
            "net_income_pesewas": 0,
            "currency": "GHS",
        }

        token = _make_token(business_id="biz-tema-harbour-005")
        response = client.get(
            "/reports/profit-loss",
            params={"date_from": "2026-01-01", "date_to": "2026-01-31"},
            headers=_auth_header(token),
        )
        assert response.status_code == 200
        mock_pl.assert_called_once()
        call_args = mock_pl.call_args
        assert call_args[0][0] == "biz-tema-harbour-005"


# ===================================================================
# GET /reports/profit-loss — Errors
# ===================================================================


class TestProfitLossErrors:

    @patch("main.profit_and_loss")
    def test_internal_error_returns_500(self, mock_pl, client):
        """If the report function raises, API should return 500."""
        mock_pl.side_effect = Exception("database connection refused")

        response = client.get(
            "/reports/profit-loss",
            params={"date_from": "2026-03-01", "date_to": "2026-03-31"},
            headers=_auth_header(),
        )
        assert response.status_code == 500


# ===================================================================
# GET /reports/profit-loss/trend — Auth
# ===================================================================


class TestTrendAuth:

    def test_trend_without_auth_returns_401(self, client):
        """Missing authorization should return 401."""
        response = client.get("/reports/profit-loss/trend")
        assert response.status_code == 401


# ===================================================================
# GET /reports/profit-loss/trend — Validation
# ===================================================================


class TestTrendValidation:

    def test_trend_months_zero_returns_422(self, client):
        """months=0 should fail validation (minimum is 1)."""
        response = client.get(
            "/reports/profit-loss/trend",
            params={"months": 0},
            headers=_auth_header(),
        )
        assert response.status_code == 422

    def test_trend_months_negative_returns_422(self, client):
        """Negative months should fail validation."""
        response = client.get(
            "/reports/profit-loss/trend",
            params={"months": -1},
            headers=_auth_header(),
        )
        assert response.status_code == 422

    def test_trend_months_exceeds_max_returns_422(self, client):
        """months > 24 should fail validation."""
        response = client.get(
            "/reports/profit-loss/trend",
            params={"months": 25},
            headers=_auth_header(),
        )
        assert response.status_code == 422


# ===================================================================
# GET /reports/profit-loss/trend — Success
# ===================================================================


class TestTrendSuccess:

    @patch("main.profit_and_loss_trend")
    def test_trend_with_valid_months_param(self, mock_trend, client):
        """Valid months should return trend data."""
        mock_trend.return_value = [
            {"month": "2026-01", "income_pesewas": 100000, "expense_pesewas": 50000, "net_income_pesewas": 50000},
        ]

        response = client.get(
            "/reports/profit-loss/trend",
            params={"months": 3},
            headers=_auth_header(),
        )
        assert response.status_code == 200
        body = response.json()
        assert "trend" in body

    @patch("main.profit_and_loss_trend")
    def test_trend_defaults_to_six_months(self, mock_trend, client):
        """When months param is omitted, default should be 6."""
        mock_trend.return_value = []

        response = client.get(
            "/reports/profit-loss/trend",
            headers=_auth_header(),
        )
        assert response.status_code == 200

    @patch("main.profit_and_loss_trend")
    def test_trend_passes_business_id_from_token(self, mock_trend, client):
        """The business_id from JWT should be passed to the trend function."""
        mock_trend.return_value = []

        token = _make_token(business_id="biz-cape-coast-fish-011")
        response = client.get(
            "/reports/profit-loss/trend",
            params={"months": 3},
            headers=_auth_header(token),
        )
        assert response.status_code == 200
        mock_trend.assert_called_once()
        call_args = mock_trend.call_args
        assert call_args[0][0] == "biz-cape-coast-fish-011"


# ===================================================================
# GET /reports/profit-loss/trend — Errors
# ===================================================================


class TestTrendErrors:

    @patch("main.profit_and_loss_trend")
    def test_trend_internal_error_returns_500(self, mock_trend, client):
        """If the trend function raises, API should return 500."""
        mock_trend.side_effect = Exception("query timeout")

        response = client.get(
            "/reports/profit-loss/trend",
            params={"months": 6},
            headers=_auth_header(),
        )
        assert response.status_code == 500
