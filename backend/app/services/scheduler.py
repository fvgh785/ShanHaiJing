from datetime import date, timedelta
from app.models import db, Plan, Record


def get_today_tasks():
    today = date.today()
    return (
        Plan.query
        .filter(Plan.planned_date == today)
        .order_by(Plan.priority.desc())
        .all()
    )


def get_kanban_data():
    plans = Plan.query.order_by(Plan.priority.desc()).all()
    kanban = {"pending": [], "in_progress": [], "completed": [], "cancelled": []}
    for plan in plans:
        status = plan.status if plan.status in kanban else "pending"
        kanban[status].append({
            "id": plan.id,
            "creature": plan.creature,
            "juan": plan.juan,
            "priority": plan.priority,
            "planned_date": plan.planned_date.isoformat() if plan.planned_date else None,
            "recommended_tool": plan.recommended_tool,
            "status": plan.status,
        })
    return kanban


def auto_complete_plan(plan_id):
    plan = db.session.get(Plan, plan_id)
    if not plan:
        return False

    records = Record.query.filter_by(plan_id=plan_id).all()
    if not records:
        return False

    all_completed = all(r.status == "completed" for r in records)
    if all_completed:
        plan.status = "completed"
        db.session.commit()
        return True
    return False
