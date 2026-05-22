import json
from datetime import date
from flask import Blueprint, request, jsonify
from app.models import db, Plan, Record, HermesLog
from app.services.scheduler import auto_complete_plan

records_bp = Blueprint("records", __name__)


def _serialize_record(record):
    return {
        "id": record.id,
        "plan_id": record.plan_id,
        "work_date": record.work_date.isoformat() if record.work_date else None,
        "creature_name": record.creature_name,
        "tools_used": json.loads(record.tools_used) if record.tools_used else [],
        "baseline_id_used": record.baseline_id_used,
        "prompt_image": record.prompt_image,
        "prompt_video": record.prompt_video,
        "negative_prompt": record.negative_prompt,
        "style_review_score": record.style_review_score,
        "style_review_suggestions": record.style_review_suggestions,
        "points_consumed": record.points_consumed,
        "output_url": record.output_url,
        "intermediate_urls": json.loads(record.intermediate_urls) if record.intermediate_urls else [],
        "notes": record.notes,
        "status": record.status,
        "hermes_skill_version": record.hermes_skill_version,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


@records_bp.route("", methods=["GET"])
def list_records():
    query = Record.query

    creature_name = request.args.get("creature_name")
    if creature_name:
        query = query.filter(Record.creature_name.ilike(f"%{creature_name}%"))

    work_date_from = request.args.get("work_date_from")
    if work_date_from:
        try:
            query = query.filter(Record.work_date >= date.fromisoformat(work_date_from))
        except ValueError:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid work_date_from format, use YYYY-MM-DD"}}), 400

    work_date_to = request.args.get("work_date_to")
    if work_date_to:
        try:
            query = query.filter(Record.work_date <= date.fromisoformat(work_date_to))
        except ValueError:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid work_date_to format, use YYYY-MM-DD"}}), 400

    status = request.args.get("status")
    if status:
        query = query.filter(Record.status == status)

    tool = request.args.get("tool")
    if tool:
        query = query.filter(Record.tools_used.contains(tool))

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    pagination = query.order_by(Record.work_date.desc(), Record.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "items": [_serialize_record(r) for r in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    })


@records_bp.route("", methods=["POST"])
def create_record():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Request body is required"}}), 400

    creature_name = data.get("creature_name")
    if not creature_name:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "creature_name is required"}}), 400

    work_date_str = data.get("work_date", date.today().isoformat())
    try:
        work_date = date.fromisoformat(work_date_str)
    except (ValueError, TypeError):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid work_date format, use YYYY-MM-DD"}}), 400

    record = Record(
        plan_id=data.get("plan_id"),
        work_date=work_date,
        creature_name=creature_name,
        tools_used=json.dumps(data.get("tools_used", [])) if isinstance(data.get("tools_used"), list) else data.get("tools_used"),
        baseline_id_used=data.get("baseline_id_used"),
        prompt_image=data.get("prompt_image"),
        prompt_video=data.get("prompt_video"),
        negative_prompt=data.get("negative_prompt"),
        style_review_score=data.get("style_review_score"),
        style_review_suggestions=data.get("style_review_suggestions"),
        points_consumed=data.get("points_consumed"),
        output_url=data.get("output_url"),
        intermediate_urls=json.dumps(data.get("intermediate_urls", [])) if isinstance(data.get("intermediate_urls"), list) else data.get("intermediate_urls"),
        notes=data.get("notes"),
        status=data.get("status", "in_progress"),
        hermes_skill_version=data.get("hermes_skill_version"),
    )

    db.session.add(record)
    db.session.commit()

    if record.plan_id and record.status == "completed":
        auto_complete_plan(record.plan_id)

    return jsonify(_serialize_record(record)), 201


@records_bp.route("/<int:record_id>", methods=["GET"])
def get_record(record_id):
    record = db.session.get(Record, record_id)
    if not record:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Record {record_id} not found"}}), 404

    result = _serialize_record(record)

    hermes_logs = HermesLog.query.filter_by(record_id=record_id).order_by(HermesLog.created_at.desc()).all()
    result["hermes_logs"] = [{
        "id": h.id,
        "record_id": h.record_id,
        "request_type": h.request_type,
        "system_prompt": h.system_prompt,
        "user_input": h.user_input,
        "response_body": h.response_body,
        "baseline_id_used": h.baseline_id_used,
        "tokens_input": h.tokens_input,
        "tokens_output": h.tokens_output,
        "api_cost": h.api_cost,
        "duration_ms": h.duration_ms,
        "adopted": h.adopted,
        "user_edited": h.user_edited,
        "error_message": h.error_message,
        "created_at": h.created_at.isoformat() if h.created_at else None,
    } for h in hermes_logs]

    return jsonify(result)


@records_bp.route("/<int:record_id>", methods=["PUT"])
def update_record(record_id):
    record = db.session.get(Record, record_id)
    if not record:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Record {record_id} not found"}}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Request body is required"}}), 400

    if "plan_id" in data:
        record.plan_id = data["plan_id"]
    if "creature_name" in data:
        record.creature_name = data["creature_name"]
    if "work_date" in data:
        try:
            record.work_date = date.fromisoformat(data["work_date"])
        except (ValueError, TypeError):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid work_date format"}}), 400
    if "tools_used" in data:
        record.tools_used = json.dumps(data["tools_used"]) if isinstance(data["tools_used"], list) else data["tools_used"]
    if "baseline_id_used" in data:
        record.baseline_id_used = data["baseline_id_used"]
    if "prompt_image" in data:
        record.prompt_image = data["prompt_image"]
    if "prompt_video" in data:
        record.prompt_video = data["prompt_video"]
    if "negative_prompt" in data:
        record.negative_prompt = data["negative_prompt"]
    if "style_review_score" in data:
        record.style_review_score = data["style_review_score"]
    if "style_review_suggestions" in data:
        record.style_review_suggestions = data["style_review_suggestions"]
    if "points_consumed" in data:
        record.points_consumed = data["points_consumed"]
    if "output_url" in data:
        record.output_url = data["output_url"]
    if "intermediate_urls" in data:
        record.intermediate_urls = json.dumps(data["intermediate_urls"]) if isinstance(data["intermediate_urls"], list) else data["intermediate_urls"]
    if "notes" in data:
        record.notes = data["notes"]
    if "status" in data:
        record.status = data["status"]
    if "hermes_skill_version" in data:
        record.hermes_skill_version = data["hermes_skill_version"]

    db.session.commit()

    if record.plan_id and record.status == "completed":
        auto_complete_plan(record.plan_id)

    return jsonify(_serialize_record(record))


@records_bp.route("/<int:record_id>", methods=["DELETE"])
def delete_record(record_id):
    record = db.session.get(Record, record_id)
    if not record:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Record {record_id} not found"}}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": f"Record {record_id} deleted"}), 200
