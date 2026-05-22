import json
import os
from datetime import datetime, date
from flask import current_app
from app.models import db, Plan, Record, HermesLog, HarmonyBaseline


def _serialize_row(row):
    if row is None:
        return None
    result = {}
    for col in row.__table__.columns:
        val = getattr(row, col.name)
        if isinstance(val, (datetime, date)):
            val = val.isoformat()
        result[col.name] = val
    return result


def export_all():
    plans = [_serialize_row(p) for p in Plan.query.all()]
    records = [_serialize_row(r) for r in Record.query.all()]
    hermes_logs = [_serialize_row(h) for h in HermesLog.query.all()]
    baselines = [_serialize_row(b) for b in HarmonyBaseline.query.all()]

    return {
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "version": "1.0",
            "counts": {
                "plans": len(plans),
                "records": len(records),
                "hermes_logs": len(hermes_logs),
                "harmony_baselines": len(baselines),
            },
        },
        "plans": plans,
        "records": records,
        "hermes_logs": hermes_logs,
        "harmony_baselines": baselines,
    }


def export_filtered(filters):
    query = Record.query

    if filters.get("creature_name"):
        query = query.filter(Record.creature_name.ilike(f"%{filters['creature_name']}%"))
    if filters.get("work_date_from"):
        query = query.filter(Record.work_date >= filters["work_date_from"])
    if filters.get("work_date_to"):
        query = query.filter(Record.work_date <= filters["work_date_to"])
    if filters.get("status"):
        query = query.filter(Record.status == filters["status"])
    if filters.get("tool"):
        query = query.filter(Record.tools_used.contains(filters["tool"]))

    records = [_serialize_row(r) for r in query.all()]
    record_ids = [r["id"] for r in records]

    plans = [_serialize_row(p) for p in Plan.query.filter(
        Plan.id.in_(
            db.session.query(Record.plan_id).filter(Record.id.in_(record_ids))
        )
    ).all()]

    hermes_logs = [_serialize_row(h) for h in HermesLog.query.filter(
        HermesLog.record_id.in_(record_ids)
    ).all()]

    baseline_ids = set()
    for r in records:
        if r.get("baseline_id_used"):
            baseline_ids.add(r["baseline_id_used"])
    for h in hermes_logs:
        if h.get("baseline_id_used"):
            baseline_ids.add(h["baseline_id_used"])
    baselines = [_serialize_row(b) for b in HarmonyBaseline.query.filter(
        HarmonyBaseline.id.in_(baseline_ids)
    ).all()]

    return {
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "version": "1.0",
            "scope": "filtered",
            "counts": {
                "plans": len(plans),
                "records": len(records),
                "hermes_logs": len(hermes_logs),
                "harmony_baselines": len(baselines),
            },
        },
        "plans": plans,
        "records": records,
        "hermes_logs": hermes_logs,
        "harmony_baselines": baselines,
    }


def import_data(json_data):
    imported = {"plans": 0, "records": 0, "hermes_logs": 0, "harmony_baselines": 0}

    model_map = {
        "plans": (Plan, "id"),
        "records": (Record, "id"),
        "hermes_logs": (HermesLog, "id"),
        "harmony_baselines": (HarmonyBaseline, "id"),
    }

    for key, (model, id_field) in model_map.items():
        items = json_data.get(key, [])
        if not items:
            continue
        for item in items:
            existing = db.session.get(model, item.get(id_field))
            if existing:
                created_at_existing = getattr(existing, "created_at", None)
                created_at_new = item.get("created_at")
                if created_at_new and created_at_existing:
                    if str(created_at_existing) == str(created_at_new):
                        continue
                for col_name, col_value in item.items():
                    if col_name != id_field and hasattr(existing, col_name):
                        setattr(existing, col_name, col_value)
            else:
                new_instance = model()
                for col_name, col_value in item.items():
                    if hasattr(new_instance, col_name):
                        setattr(new_instance, col_name, col_value)
                db.session.add(new_instance)
                imported[key] += 1

    db.session.commit()
    return imported


def get_backup_list():
    backup_dir = current_app.config["BACKUP_DIR"]
    if not os.path.isdir(backup_dir):
        return []

    files = []
    for fname in os.listdir(backup_dir):
        fpath = os.path.join(backup_dir, fname)
        if os.path.isfile(fpath):
            stat = os.stat(fpath)
            files.append({
                "name": fname,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

    files.sort(key=lambda f: f["modified_at"], reverse=True)
    return files
