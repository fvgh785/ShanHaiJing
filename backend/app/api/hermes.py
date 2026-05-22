import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from app.models import db, HermesLog
from app.hermes_client import HermesClient, HermesException
from app.hermes_client.retry import CircuitBreakerOpen

hermes_bp = Blueprint("hermes", __name__)


def _get_client():
    return HermesClient(
        base_url=current_app.config["HERMES_BASE_URL"],
        timeout=current_app.config["HERMES_TIMEOUT"],
        max_retries=current_app.config["HERMES_MAX_RETRIES"],
        circuit_threshold=current_app.config["HERMES_CIRCUIT_BREAK_THRESHOLD"],
        circuit_cooldown=current_app.config["HERMES_CIRCUIT_BREAK_COOLDOWN"],
    )


@hermes_bp.route("/generate-prompt", methods=["POST"])
def generate_prompt():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Request body is required"}}), 400

    creature_name = data.get("creature_name")
    if not creature_name:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "creature_name is required"}}), 400

    juan = data.get("juan")
    style_tag = data.get("style_tag")
    baseline_id = data.get("baseline_id")
    record_id = data.get("record_id")

    start_time = datetime.utcnow()

    try:
        client = _get_client()
        result = client.generate_prompt(
            creature_name=creature_name,
            juan=juan,
            style_tag=style_tag,
            baseline_id=baseline_id,
        )
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        log = HermesLog(
            record_id=record_id,
            request_type="prompt_generation",
            user_input=json.dumps({
                "creature_name": creature_name,
                "juan": juan,
                "style_tag": style_tag,
            }, ensure_ascii=False),
            response_body=json.dumps(result, ensure_ascii=False),
            baseline_id_used=baseline_id,
            tokens_input=result.get("tokens_input"),
            tokens_output=result.get("tokens_output"),
            api_cost=result.get("api_cost"),
            duration_ms=duration_ms,
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "image_prompt": result.get("image_prompt"),
            "video_prompt": result.get("video_prompt"),
            "negative_prompt": result.get("negative_prompt"),
            "log_id": log.id,
        })

    except CircuitBreakerOpen as e:
        cooldown = _get_client().circuit_breaker.remaining_cooldown()
        error_msg = (
            f"AI service is currently unavailable (cooling down). "
            f"Please try again in {int(cooldown)} seconds or enter prompts manually."
        )
        return jsonify({"error": {"code": "CIRCUIT_OPEN", "message": error_msg}}), 503

    except HermesException as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log = HermesLog(
            record_id=record_id,
            request_type="prompt_generation",
            user_input=json.dumps({
                "creature_name": creature_name,
                "juan": juan,
                "style_tag": style_tag,
            }, ensure_ascii=False),
            error_message=str(e),
            duration_ms=duration_ms,
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "error": {
                "code": "HERMES_ERROR",
                "message": "AI service temporarily unavailable, please try again or enter prompts manually",
            },
            "log_id": log.id,
        }), 503


@hermes_bp.route("/review-style", methods=["POST"])
def review_style():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Request body is required"}}), 400

    generated_prompt = data.get("generated_prompt")
    if not generated_prompt:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "generated_prompt is required"}}), 400

    baseline_id = data.get("baseline_id")
    record_id = data.get("record_id")

    start_time = datetime.utcnow()

    try:
        client = _get_client()
        result = client.review_style(
            generated_prompt=generated_prompt,
            baseline_id=baseline_id,
        )
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        log = HermesLog(
            record_id=record_id,
            request_type="style_review",
            user_input=json.dumps({"generated_prompt": generated_prompt}, ensure_ascii=False),
            response_body=json.dumps(result, ensure_ascii=False),
            baseline_id_used=baseline_id,
            tokens_input=result.get("tokens_input"),
            tokens_output=result.get("tokens_output"),
            api_cost=result.get("api_cost"),
            duration_ms=duration_ms,
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "overall_score": result.get("overall_score"),
            "dimension_scores": result.get("dimension_scores", {}),
            "suggestions": result.get("suggestions"),
            "log_id": log.id,
        })

    except CircuitBreakerOpen as e:
        cooldown = _get_client().circuit_breaker.remaining_cooldown()
        error_msg = (
            f"AI service is currently unavailable (cooling down). "
            f"Please try again in {int(cooldown)} seconds or enter prompts manually."
        )
        return jsonify({"error": {"code": "CIRCUIT_OPEN", "message": error_msg}}), 503

    except HermesException as e:
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log = HermesLog(
            record_id=record_id,
            request_type="style_review",
            user_input=json.dumps({"generated_prompt": generated_prompt}, ensure_ascii=False),
            error_message=str(e),
            duration_ms=duration_ms,
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "error": {
                "code": "HERMES_ERROR",
                "message": "AI service temporarily unavailable, please try again or enter prompts manually",
            },
            "log_id": log.id,
        }), 503


@hermes_bp.route("/logs", methods=["GET"])
def list_logs():
    query = HermesLog.query

    record_id = request.args.get("record_id", type=int)
    if record_id:
        query = query.filter(HermesLog.record_id == record_id)

    request_type = request.args.get("request_type")
    if request_type:
        query = query.filter(HermesLog.request_type == request_type)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    pagination = query.order_by(HermesLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "items": [{
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
        } for h in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    })
