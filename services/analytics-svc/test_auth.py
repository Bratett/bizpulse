"""Unit tests for JWT authentication in the analytics service.

Tests cover the get_current_user dependency: valid tokens, missing headers,
invalid tokens, expired tokens, and claim extraction.

Uses python-jose to generate real JWT tokens with a test secret.
"""

import time
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from jose import jwt

# Test secret — used only in tests, never in production
TEST_JWT_SECRET = "test-secret-for-analytics-svc-unit-tests"

# Realistic Ghanaian business claims
TEST_CLAIMS = {
    "sub": "user-kwame-001",
    "business_id": "biz-accra-traders-042",
    "role": "owner",
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600,  # 1 hour from now
}


def _make_token(claims: dict, secret: str = TEST_JWT_SECRET) -> str:
    """Helper: create a signed HS256 JWT."""
    return jwt.encode(claims, secret, algorithm="HS256")


def _make_request(headers: dict = None, cookies: dict = None):
    """Helper: create a mock FastAPI Request object."""
    from unittest.mock import MagicMock

    request = MagicMock()
    request.headers = headers or {}
    request.cookies = cookies or {}
    return request


class TestGetCurrentUserValidToken:
    """Tests for successful authentication with a valid Bearer token."""

    @patch("auth.settings")
    def test_valid_bearer_token_returns_user_dict(self, mock_settings):
        """A valid Bearer token should return a dict with user_id, business_id, role."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET
        token = _make_token(TEST_CLAIMS)
        request = _make_request(headers={"Authorization": f"Bearer {token}"})

        user = get_current_user(request)

        assert user["user_id"] == "user-kwame-001"
        assert user["business_id"] == "biz-accra-traders-042"
        assert user["role"] == "owner"

    @patch("auth.settings")
    def test_valid_token_in_cookie(self, mock_settings):
        """When no Authorization header is present, token should be read from cookie."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET
        token = _make_token(TEST_CLAIMS)
        request = _make_request(cookies={"token": token})

        user = get_current_user(request)

        assert user["user_id"] == "user-kwame-001"
        assert user["business_id"] == "biz-accra-traders-042"

    @patch("auth.settings")
    def test_bearer_token_takes_precedence_over_cookie(self, mock_settings):
        """Authorization header should be preferred over cookie when both are present."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET

        header_claims = {**TEST_CLAIMS, "sub": "user-from-header"}
        cookie_claims = {**TEST_CLAIMS, "sub": "user-from-cookie"}

        header_token = _make_token(header_claims)
        cookie_token = _make_token(cookie_claims)

        request = _make_request(
            headers={"Authorization": f"Bearer {header_token}"},
            cookies={"token": cookie_token},
        )

        user = get_current_user(request)
        assert user["user_id"] == "user-from-header"


class TestGetCurrentUserMissingAuth:
    """Tests for requests without any authentication credential."""

    @patch("auth.settings")
    def test_missing_authorization_header_raises_401(self, mock_settings):
        """Request with no Authorization header and no cookie should raise 401."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET
        request = _make_request()

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "UNAUTHORIZED"
        assert "Missing" in exc_info.value.detail["error"]["message"]

    @patch("auth.settings")
    def test_empty_authorization_header_raises_401(self, mock_settings):
        """An empty Authorization header (no Bearer prefix) should raise 401."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET
        request = _make_request(headers={"Authorization": ""})

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401

    @patch("auth.settings")
    def test_non_bearer_scheme_raises_401(self, mock_settings):
        """Authorization header with a scheme other than Bearer should raise 401."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET
        token = _make_token(TEST_CLAIMS)
        request = _make_request(headers={"Authorization": f"Basic {token}"})

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401


class TestGetCurrentUserInvalidToken:
    """Tests for requests with malformed or tampered tokens."""

    @patch("auth.settings")
    def test_garbage_token_raises_401(self, mock_settings):
        """A completely invalid token string should raise 401."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET
        request = _make_request(headers={"Authorization": "Bearer not.a.valid.jwt"})

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "UNAUTHORIZED"

    @patch("auth.settings")
    def test_wrong_secret_raises_401(self, mock_settings):
        """A token signed with a different secret should fail validation."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET
        token = _make_token(TEST_CLAIMS, secret="wrong-secret-entirely")
        request = _make_request(headers={"Authorization": f"Bearer {token}"})

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401

    @patch("auth.settings")
    def test_tampered_payload_raises_401(self, mock_settings):
        """A token with a tampered payload (broken signature) should raise 401."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET
        token = _make_token(TEST_CLAIMS)

        # Tamper with the payload segment (middle part)
        parts = token.split(".")
        parts[1] = parts[1][:-4] + "XXXX"  # corrupt payload
        tampered = ".".join(parts)

        request = _make_request(headers={"Authorization": f"Bearer {tampered}"})

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401


class TestGetCurrentUserExpiredToken:
    """Tests for tokens that have expired."""

    @patch("auth.settings")
    def test_expired_token_raises_401(self, mock_settings):
        """A token with an exp claim in the past should raise 401."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET

        expired_claims = {
            **TEST_CLAIMS,
            "iat": int(time.time()) - 7200,  # issued 2 hours ago
            "exp": int(time.time()) - 3600,  # expired 1 hour ago
        }
        token = _make_token(expired_claims)
        request = _make_request(headers={"Authorization": f"Bearer {token}"})

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired" in exc_info.value.detail["error"]["message"]


class TestGetCurrentUserClaimExtraction:
    """Tests verifying correct extraction of business_id and other claims."""

    @patch("auth.settings")
    def test_extracts_business_id_from_claims(self, mock_settings):
        """The business_id claim should be correctly extracted for downstream use."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET

        claims = {
            "sub": "user-yaa-003",
            "business_id": "biz-kumasi-textiles-099",
            "role": "accountant",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = _make_token(claims)
        request = _make_request(headers={"Authorization": f"Bearer {token}"})

        user = get_current_user(request)

        assert user["business_id"] == "biz-kumasi-textiles-099"
        assert user["user_id"] == "user-yaa-003"
        assert user["role"] == "accountant"

    @patch("auth.settings")
    def test_missing_optional_claims_return_none(self, mock_settings):
        """If business_id or role are missing from the token, they should be None."""
        from auth import get_current_user

        mock_settings.JWT_SECRET = TEST_JWT_SECRET

        minimal_claims = {
            "sub": "user-minimal",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        token = _make_token(minimal_claims)
        request = _make_request(headers={"Authorization": f"Bearer {token}"})

        user = get_current_user(request)

        assert user["user_id"] == "user-minimal"
        assert user["business_id"] is None
        assert user["role"] is None
