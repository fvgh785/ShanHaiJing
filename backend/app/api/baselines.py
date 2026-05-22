import json
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from app.models import db, HarmonyBaseline

baselines_bp = Blueprint("baselines", __name__)


def _serialize_baseline(b):
    return {
        "id": b.id,
        "name": b.name,
        "version": b.version,
        "tool_type": b.tool_type,
        "style_tags": json.loads(b.style_tags) if b.style_tags else [],
        "prompt_template": b.prompt_template,
        "file_path": b.file_path,
        "is_active": b.is_active,
        "previous_id": b.previous_id,
        "source_record_id": b.source_record_id,
        "rating": b.rating,
        "usage_count": b.usage_count,
        "created_at": b.created_at.isoformat() if b.created_at else None,
    }


def _write_baseline_file(baseline):
    harmony_dir = current_app.config["HARMONY_DIR"]
    os.makedirs(harmony_dir, exist_ok=True)

    filename = f"{baseline.name.replace(' ', '_')}_v{baseline.version}.md"
    file_path = os.path.join(harmony_dir, filename)

    content = f"""# {baseline.name} v{baseline.version}

**Tool Type:** {baseline.tool_type}
**Style Tags:** {', '.join(json.loads(baseline.style_tags) if baseline.style_tags else [])}
**Version:** {baseline.version}
**Created:** {datetime.utcnow().isoformat()}

## Prompt Template

{baseline.prompt_template}
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path


def _get_version_chain(baseline_id):
    chain = []
    current = db.session.get(HarmonyBaseline, baseline_id)
    while current:
        chain.append({
            "id": current.id,
            "version": current.version,
            "name": current.name,
            "is_active": current.is_active,
            "created_at": current.created_at.isoformat() if current.created_at else None,
        })
        current = db.session.get(HarmonyBaseline, current.previous_id) if current.previous_id else None
    return chain


@baselines_bp.route("", methods=["GET"])
def list_baselines():
    query = HarmonyBaseline.query

    is_active = request.args.get("is_active")
    if is_active is not None:
        if is_active.lower() == "true":
            query = query.filter(HarmonyBaseline.is_active == True)

    baselines = query.order_by(HarmonyBaseline.created_at.desc()).all()
    return jsonify([_serialize_baseline(b) for b in baselines])


@baselines_bp.route("", methods=["POST"])
def create_baseline():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Request body is required"}}), 400

    name = data.get("name")
    tool_type = data.get("tool_type")
    prompt_template = data.get("prompt_template")

    if not name:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "name is required"}}), 400
    if not tool_type:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "tool_type is required"}}), 400
    if not prompt_template:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "prompt_template is required"}}), 400

    style_tags = data.get("style_tags", [])
    if isinstance(style_tags, list):
        style_tags = json.dumps(style_tags, ensure_ascii=False)

    baseline = HarmonyBaseline(
        name=name,
        version=1,
        tool_type=tool_type,
        style_tags=style_tags,
        prompt_template=prompt_template,
        source_record_id=data.get("source_record_id"),
        rating=data.get("rating"),
    )

    db.session.add(baseline)
    db.session.flush()

    file_path = _write_baseline_file(baseline)
    baseline.file_path = file_path

    db.session.commit()

    return jsonify(_serialize_baseline(baseline)), 201


@baselines_bp.route("/<int:baseline_id>", methods=["GET"])
def get_baseline(baseline_id):
    baseline = db.session.get(HarmonyBaseline, baseline_id)
    if not baseline:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Baseline {baseline_id} not found"}}), 404

    return jsonify(_serialize_baseline(baseline))


@baselines_bp.route("/<int:baseline_id>", methods=["PUT"])
def update_baseline(baseline_id):
    old_baseline = db.session.get(HarmonyBaseline, baseline_id)
    if not old_baseline:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Baseline {baseline_id} not found"}}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Request body is required"}}), 400

    style_tags = data.get("style_tags", json.loads(old_baseline.style_tags) if old_baseline.style_tags else [])
    if isinstance(style_tags, list):
        style_tags = json.dumps(style_tags, ensure_ascii=False)

    new_baseline = HarmonyBaseline(
        name=data.get("name", old_baseline.name),
        version=old_baseline.version + 1,
        tool_type=data.get("tool_type", old_baseline.tool_type),
        style_tags=style_tags,
        prompt_template=data.get("prompt_template", old_baseline.prompt_template),
        source_record_id=data.get("source_record_id", old_baseline.source_record_id),
        rating=data.get("rating", old_baseline.rating),
        is_active=old_baseline.is_active,
        previous_id=old_baseline.id,
        usage_count=0,
    )

    db.session.add(new_baseline)
    db.session.flush()

    file_path = _write_baseline_file(new_baseline)
    new_baseline.file_path = file_path

    db.session.commit()

    return jsonify(_serialize_baseline(new_baseline)), 201


@baselines_bp.route("/<int:baseline_id>", methods=["DELETE"])
def delete_baseline(baseline_id):
    baseline = db.session.get(HarmonyBaseline, baseline_id)
    if not baseline:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Baseline {baseline_id} not found"}}), 404

    baseline.is_active = False
    db.session.commit()

    return jsonify({"message": f"Baseline {baseline_id} soft-deleted", "is_active": False})


@baselines_bp.route("/<int:baseline_id>/activate", methods=["POST"])
def activate_baseline(baseline_id):
    baseline = db.session.get(HarmonyBaseline, baseline_id)
    if not baseline:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Baseline {baseline_id} not found"}}), 404

    HarmonyBaseline.query.filter(
        HarmonyBaseline.tool_type == baseline.tool_type,
        HarmonyBaseline.id != baseline_id,
    ).update({"is_active": False})

    baseline.is_active = True
    db.session.commit()

    return jsonify({
        "id": baseline.id,
        "name": baseline.name,
        "tool_type": baseline.tool_type,
        "is_active": True,
    })


@baselines_bp.route("/<int:baseline_id>/versions", methods=["GET"])
def get_baseline_versions(baseline_id):
    baseline = db.session.get(HarmonyBaseline, baseline_id)
    if not baseline:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Baseline {baseline_id} not found"}}), 404

    versions = _get_version_chain(baseline_id)
    return jsonify({"versions": versions})
