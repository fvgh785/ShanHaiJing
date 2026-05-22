from datetime import date
from app.models import db, DailyQuota

TOOL_MAPPING = {
    "即梦AI": "jimeng",
    "小云雀": "seedance",
}


def get_today_quotas():
    today = date.today()
    quota = DailyQuota.query.filter_by(date=today).first()
    if not quota:
        quota = DailyQuota(
            date=today,
            jimeng_total=100,
            jimeng_used=0,
            seedance_total=130,
            seedance_used=0,
        )
        db.session.add(quota)
        db.session.commit()
    return quota


def update_quota(tool, amount=1):
    if tool not in TOOL_MAPPING:
        raise ValueError(f"Unknown tool: {tool}. Must be one of {list(TOOL_MAPPING.keys())}")

    quota = get_today_quotas()
    field = f"{TOOL_MAPPING[tool]}_used"
    current = getattr(quota, field, 0)
    setattr(quota, field, current + amount)
    db.session.commit()
    return quota


def get_quota_summary():
    quota = get_today_quotas()
    return {
        "jimeng": {
            "total": quota.jimeng_total,
            "used": quota.jimeng_used,
            "remaining": max(0, quota.jimeng_total - quota.jimeng_used),
        },
        "seedance": {
            "total": quota.seedance_total,
            "used": quota.seedance_used,
            "remaining": max(0, quota.seedance_total - quota.seedance_used),
        },
    }
