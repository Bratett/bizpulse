import os
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from auth import get_current_user
from config import settings
from reports import profit_and_loss, profit_and_loss_trend

app = FastAPI(title="BizPulse Analytics Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "analytics-svc"}


@app.get("/reports/profit-loss")
async def get_profit_loss(
    date_from: date = Query(default=None, description="Start date (YYYY-MM-DD)"),
    date_to: date = Query(default=None, description="End date (YYYY-MM-DD)"),
    user: dict = Depends(get_current_user),
):
    """Generate a Profit & Loss statement for the authenticated business.

    Defaults to current month if no dates provided.
    All monetary values are in pesewas (divide by 100 for cedis).
    """
    if date_from is None:
        date_from = date.today().replace(day=1)
    if date_to is None:
        date_to = date.today()

    if date_from > date_to:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_DATE_RANGE", "message": "date_from must be before date_to"}},
        )

    try:
        report = profit_and_loss(user["business_id"], date_from, date_to)
        return report
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Failed to generate report"}},
        )


@app.get("/reports/profit-loss/trend")
async def get_profit_loss_trend(
    months: int = Query(default=6, ge=1, le=24, description="Number of months to include"),
    user: dict = Depends(get_current_user),
):
    """Month-over-month P&L trend for the authenticated business."""
    try:
        trend = profit_and_loss_trend(user["business_id"], months)
        return {"trend": trend, "months_requested": months}
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Failed to generate trend"}},
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("ANALYTICS_SVC_PORT", "8081"))
    uvicorn.run(app, host="0.0.0.0", port=port)
