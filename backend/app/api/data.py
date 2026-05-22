import json
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from app.models import db
from app.services.exporter import export_all, export_filtered, import_data, get_backup_list

data_bp = Blueprint("data", __name__)


@data_bp.route("/export", methods=["GET"])
def export_json():
    scope = request.args.get("scope", "full")

    if scope == "filtered":
        filters = {
            "creature_name": request.args.get("creature_name"),
            "work_date_from": request.args.get("work_date_from"),
            "work_date_to": request.args.get("work_date_to"),
            "status": request.args.get("status"),
            "tool": request.args.get("tool"),
        }
        filters = {k: v for k, v in filters.items() if v}
        result = export_filtered(filters)
    else:
        result = export_all()

    return jsonify(result)


@data_bp.route("/import", methods=["POST"])
def import_json():
    if "file" not in request.files:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "No file provided"}}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.endswith(".json"):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "File must be a JSON file"}}), 400

    try:
        content = file.read().decode("utf-8")
        json_data = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": f"Invalid JSON file: {str(e)}"}}), 400

    required_keys = ["export_metadata", "plans", "records"]
    for key in required_keys:
        if key not in json_data:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": f"Missing required key: {key}"}}), 400

    try:
        imported = import_data(json_data)
        return jsonify({"imported": imported})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"code": "IMPORT_ERROR", "message": str(e)}}), 500


@data_bp.route("/backups", methods=["GET"])
def list_backups():
    files = get_backup_list()
    return jsonify({"backups": files})
