from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models import UsageEvent, User
from app.schemas import AdminStatsResponse, UsageByDay, UsageByUser, UsageTotals

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
) -> AdminStatsResponse:
    """Aggregate usage totals, per-user breakdown, and a requests-over-time
    series for the admin dashboard. Restricted to is_admin users."""
    since = date.today() - timedelta(days=days)

    totals_row = (
        db.query(
            func.count(UsageEvent.id),
            func.coalesce(func.sum(UsageEvent.prompt_tokens), 0),
            func.coalesce(func.sum(UsageEvent.completion_tokens), 0),
            func.coalesce(func.avg(UsageEvent.latency_ms), 0.0),
        )
        .filter(UsageEvent.created_at >= since)
        .one()  # ungrouped aggregate always yields exactly one row (zeros if no matches)
    )
    totals = UsageTotals(
        total_requests=totals_row[0] or 0,
        total_prompt_tokens=int(totals_row[1] or 0),
        total_completion_tokens=int(totals_row[2] or 0),
        avg_latency_ms=round(float(totals_row[3] or 0.0), 1),
    )

    by_user_rows = (
        db.query(
            UsageEvent.user_id,
            User.email,
            func.count(UsageEvent.id),
            func.coalesce(func.sum(UsageEvent.prompt_tokens + UsageEvent.completion_tokens), 0),
        )
        .outerjoin(User, User.id == UsageEvent.user_id)
        .filter(UsageEvent.created_at >= since)
        .group_by(UsageEvent.user_id, User.email)
        .order_by(func.count(UsageEvent.id).desc())
        .limit(20)
        .all()
    )
    by_user = [
        UsageByUser(user_id=r[0], email=r[1], requests=r[2], total_tokens=int(r[3] or 0))
        for r in by_user_rows
    ]

    by_day_rows = (
        db.query(
            func.date(UsageEvent.created_at),
            func.count(UsageEvent.id),
            func.coalesce(func.sum(UsageEvent.prompt_tokens + UsageEvent.completion_tokens), 0),
        )
        .filter(UsageEvent.created_at >= since)
        .group_by(func.date(UsageEvent.created_at))
        .order_by(func.date(UsageEvent.created_at))
        .all()
    )
    by_day = [
        UsageByDay(date=str(r[0]), requests=r[1], total_tokens=int(r[2] or 0)) for r in by_day_rows
    ]

    return AdminStatsResponse(totals=totals, by_user=by_user, by_day=by_day)
