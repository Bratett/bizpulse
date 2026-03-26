from fastapi import HTTPException, Request
from jose import JWTError, jwt

from config import settings


def get_current_user(request: Request) -> dict:
    """Dual-mode auth: Kong-forwarded headers OR legacy HS256 JWT.

    Mode 1 (Kong path): If X-User-Id header is present, Kong has already
    validated the JWT via its JWT plugin. Trust the forwarded headers.

    Mode 2 (Legacy path): If no Kong headers, fall back to HS256 JWT
    validation using the shared secret.

    This dual-mode approach allows gradual migration to Keycloak/Kong (ADR-0017).
    """
    # Kong-forwarded path: headers already verified by Kong JWT plugin
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return {
            "user_id": user_id,
            "business_id": request.headers.get("X-Business-Id"),
            "role": request.headers.get("X-Roles", ""),
        }

    # Legacy HS256 JWT path
    token = None

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    if not token:
        token = request.cookies.get("token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Missing authorization"}},
        )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return {
            "user_id": payload.get("sub"),
            "business_id": payload.get("business_id"),
            "role": payload.get("role"),
        }
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid or expired token"}},
        )
