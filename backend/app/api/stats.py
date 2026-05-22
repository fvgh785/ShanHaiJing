import json
from datetime import date, timedelta
from collections import Counter
from flask import Blueprint, jsonify
from sqlalchemy import func
from app.models import db, Plan, Record, DailyQuota
from app.services.quota_tracker import get_quota_summary

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("", methods=["GET"])
def get_stats():
    today = date.today()

    today_tasks = Plan.query.filter(Plan.planned_date == today).count()
    today_completed = Plan.query.filter(
        Plan.planned_date == today,
        Plan.status == "completed",
    ).count()

    seven_days_ago = today - timedelta(days=6)
    daily_counts = (
        db.session.query(Plan.planned_date, func.count(Plan.id))
        .filter(Plan.planned_date >= seven_days_ago, Plan.planned_date <= today)
        .group_by(Plan.planned_date)
        .order_by(Plan.planned_date)
        .all()
    )

    daily_completed = (
        db.session.query(Plan.planned_date, func.count(Plan.id))
        .filter(
            Plan.planned_date >= seven_days_ago,
            Plan.planned_date <= today,
            Plan.status == "completed",
        )
        .group_by(Plan.planned_date)
        .order_by(Plan.planned_date)
        .all()
    )

    completed_map = {str(d): c for d, c in daily_completed}

    daily_data = []
    for i in range(7):
        d = seven_days_ago + timedelta(days=i)
        total_count = 0
        completed_count = 0
        for dt, count in daily_counts:
            if dt == d:
                total_count = count
                break
        completed_count = completed_map.get(str(d), 0)
        daily_data.append({
            "date": d.isoformat(),
            "total": total_count,
            "completed": completed_count,
        })

    records = Record.query.all()
    tools_counter = Counter()
    for r in records:
        if r.tools_used:
            try:
                tools = json.loads(r.tools_used)
                for tool in tools:
                    tools_counter[tool] += 1
            except (json.JSONDecodeError, TypeError):
                pass

    tools_usage = [{"tool": tool, "count": count}
                   for tool, count in tools_counter.most_common()]

    points_records = (
        db.session.query(Record.work_date, func.sum(Record.points_consumed))
        .filter(Record.work_date >= seven_days_ago, Record.points_consumed.isnot(None))
        .group_by(Record.work_date)
        .order_by(Record.work_date)
        .all()
    )

    points_map = {str(d): p for d, p in points_records}
    points_trend = []
    for i in range(7):
        d = seven_days_ago + timedelta(days=i)
        points_trend.append({
            "date": d.isoformat(),
            "points": points_map.get(str(d), 0) or 0,
        })

    quotas = get_quota_summary()

    return jsonify({
        "today_tasks": today_tasks,
        "today_completed": today_completed,
        "daily_counts": daily_data,
        "tools_usage": tools_usage,
        "points_trend": points_trend,
        "quotas": quotas,
    })
