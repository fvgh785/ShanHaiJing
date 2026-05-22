import csv
import io
from datetime import date, datetime
from flask import Blueprint, request, jsonify
from app.models import db, Plan, Record

plans_bp = Blueprint("plans", __name__)


@plans_bp.route("", methods=["GET"])
def list_plans():
    query = Plan.query

    status = request.args.get("status")
    if status:
        query = query.filter(Plan.status == status)

    date_from = request.args.get("date_from")
    if date_from:
        try:
            query = query.filter(Plan.planned_date >= date.fromisoformat(date_from))
        except ValueError:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid date_from format, use YYYY-MM-DD"}}), 400

    date_to = request.args.get("date_to")
    if date_to:
        try:
            query = query.filter(Plan.planned_date <= date.fromisoformat(date_to))
        except ValueError:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid date_to format, use YYYY-MM-DD"}}), 400

    plans = query.order_by(Plan.priority.desc(), Plan.planned_date.asc()).all()
    return jsonify([{
        "id": p.id,
        "creature": p.creature,
        "juan": p.juan,
        "priority": p.priority,
        "planned_date": p.planned_date.isoformat() if p.planned_date else None,
        "recommended_tool": p.recommended_tool,
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    } for p in plans])


@plans_bp.route("", methods=["POST"])
def create_plan():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Request body is required"}}), 400

    creature = data.get("creature")
    if not creature:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "creature is required"}}), 400

    planned_date_str = data.get("planned_date", date.today().isoformat())
    try:
        planned_date = date.fromisoformat(planned_date_str)
    except (ValueError, TypeError):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid planned_date format, use YYYY-MM-DD"}}), 400

    plan = Plan(
        creature=creature,
        juan=data.get("juan"),
        priority=data.get("priority", 3),
        planned_date=planned_date,
        recommended_tool=data.get("recommended_tool"),
        status=data.get("status", "pending"),
    )

    db.session.add(plan)
    db.session.commit()

    return jsonify({
        "id": plan.id,
        "creature": plan.creature,
        "juan": plan.juan,
        "priority": plan.priority,
        "planned_date": plan.planned_date.isoformat() if plan.planned_date else None,
        "recommended_tool": plan.recommended_tool,
        "status": plan.status,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }), 201


@plans_bp.route("/<int:plan_id>", methods=["GET"])
def get_plan(plan_id):
    plan = db.session.get(Plan, plan_id)
    if not plan:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Plan {plan_id} not found"}}), 404

    return jsonify({
        "id": plan.id,
        "creature": plan.creature,
        "juan": plan.juan,
        "priority": plan.priority,
        "planned_date": plan.planned_date.isoformat() if plan.planned_date else None,
        "recommended_tool": plan.recommended_tool,
        "status": plan.status,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    })


@plans_bp.route("/<int:plan_id>", methods=["PUT"])
def update_plan(plan_id):
    plan = db.session.get(Plan, plan_id)
    if not plan:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Plan {plan_id} not found"}}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Request body is required"}}), 400

    if "creature" in data:
        plan.creature = data["creature"]
    if "juan" in data:
        plan.juan = data["juan"]
    if "priority" in data:
        plan.priority = data["priority"]
    if "recommended_tool" in data:
        plan.recommended_tool = data["recommended_tool"]
    if "status" in data:
        plan.status = data["status"]
    if "planned_date" in data:
        try:
            plan.planned_date = date.fromisoformat(data["planned_date"])
        except (ValueError, TypeError):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid planned_date format, use YYYY-MM-DD"}}), 400

    db.session.commit()

    return jsonify({
        "id": plan.id,
        "creature": plan.creature,
        "juan": plan.juan,
        "priority": plan.priority,
        "planned_date": plan.planned_date.isoformat() if plan.planned_date else None,
        "recommended_tool": plan.recommended_tool,
        "status": plan.status,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    })


@plans_bp.route("/<int:plan_id>", methods=["DELETE"])
def delete_plan(plan_id):
    plan = db.session.get(Plan, plan_id)
    if not plan:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Plan {plan_id} not found"}}), 404

    db.session.delete(plan)
    db.session.commit()
    return jsonify({"message": f"Plan {plan_id} deleted"}), 200


@plans_bp.route("/import", methods=["POST"])
def import_plans():
    if "file" not in request.files:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "No file provided"}}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.endswith(".csv"):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "File must be a CSV"}}), 400

    try:
        content = file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            file.seek(0)
            content = file.read().decode("gbk")
        except UnicodeDecodeError:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Unable to decode file encoding"}}), 400

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "CSV has no headers"}}), 400

    created = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        creature = row.get("creature", "").strip()
        if not creature:
            errors.append({"row": row_num, "error": "creature is required"})
            continue

        planned_date_str = row.get("planned_date", "").strip()
        try:
            planned_date = date.fromisoformat(planned_date_str) if planned_date_str else date.today()
        except ValueError:
            errors.append({"row": row_num, "error": f"Invalid planned_date: {planned_date_str}"})
            continue

        priority_str = row.get("priority", "3").strip()
        try:
            priority = int(priority_str)
        except ValueError:
            priority = 3

        plan = Plan(
            creature=creature,
            juan=row.get("juan", "").strip() or None,
            priority=priority,
            planned_date=planned_date,
            recommended_tool=row.get("recommended_tool", "").strip() or None,
            status=row.get("status", "pending").strip() or "pending",
        )
        db.session.add(plan)
        created += 1

    db.session.commit()

    return jsonify({
        "created": created,
        "errors": errors,
    }), 201


@plans_bp.route("/<int:plan_id>/status", methods=["PATCH"])
def update_plan_status(plan_id):
    plan = db.session.get(Plan, plan_id)
    if not plan:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Plan {plan_id} not found"}}), 404

    data = request.get_json(silent=True)
    if not data or "status" not in data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "status is required"}}), 400

    valid_statuses = {"pending", "in_progress", "completed", "cancelled"}
    new_status = data["status"]
    if new_status not in valid_statuses:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": f"Invalid status. Must be one of {valid_statuses}"}}), 400

    plan.status = new_status
    db.session.commit()

    return jsonify({
        "id": plan.id,
        "status": plan.status,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    })
