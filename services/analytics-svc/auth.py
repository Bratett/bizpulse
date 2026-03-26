from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt

from config import settings


def get_current_user(request: Request) -> dict:
    """Extract and validate JWT from Authorization header or cookie."""
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
