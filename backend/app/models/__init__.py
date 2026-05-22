from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Index
from datetime import datetime, date

db = SQLAlchemy()


class Plan(db.Model):
    __tablename__ = 'plans'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creature = db.Column(db.String(100), nullable=False)
    juan = db.Column(db.String(50))
    priority = db.Column(db.Integer, default=3)
    planned_date = db.Column(db.Date, nullable=False, default=date.today)
    recommended_tool = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')  # pending|in_progress|completed|cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    records = db.relationship('Record', back_populates='plan')

    __table_args__ = (
        Index('idx_plans_status_date', 'status', 'planned_date'),
    )


class Record(db.Model):
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_id = db.Column(db.Integer, ForeignKey('plans.id'), nullable=True)
    work_date = db.Column(db.Date, nullable=False, default=date.today)
    creature_name = db.Column(db.String(100), nullable=False)
    tools_used = db.Column(db.Text)  # JSON array
    baseline_id_used = db.Column(db.Integer, ForeignKey('harmony_baselines.id'), nullable=True)
    prompt_image = db.Column(db.Text)
    prompt_video = db.Column(db.Text)
    negative_prompt = db.Column(db.Text)
    style_review_score = db.Column(db.Float)
    style_review_suggestions = db.Column(db.Text)
    points_consumed = db.Column(db.Integer)
    output_url = db.Column(db.Text)
    intermediate_urls = db.Column(db.Text)  # JSON array
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='in_progress')  # in_progress|completed|failed
    hermes_skill_version = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    plan = db.relationship('Plan', back_populates='records')
    hermes_logs = db.relationship('HermesLog', back_populates='record')
    baseline = db.relationship('HarmonyBaseline', foreign_keys=[baseline_id_used],
                               back_populates='records_using')

    __table_args__ = (
        Index('idx_records_creature', 'creature_name'),
        Index('idx_records_date', 'work_date'),
        Index('idx_records_status', 'status'),
    )


class HermesLog(db.Model):
    __tablename__ = 'hermes_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    record_id = db.Column(db.Integer, ForeignKey('records.id'), nullable=True)
    request_type = db.Column(db.String(30), nullable=False)  # prompt_generation|style_review
    system_prompt = db.Column(db.Text)
    user_input = db.Column(db.Text)
    response_body = db.Column(db.Text)
    baseline_id_used = db.Column(db.Integer, ForeignKey('harmony_baselines.id'), nullable=True)
    tokens_input = db.Column(db.Integer)
    tokens_output = db.Column(db.Integer)
    api_cost = db.Column(db.Float)
    duration_ms = db.Column(db.Integer)
    adopted = db.Column(db.Boolean, default=False)
    user_edited = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    record = db.relationship('Record', back_populates='hermes_logs')
    baseline = db.relationship('HarmonyBaseline', foreign_keys=[baseline_id_used])

    __table_args__ = (
        Index('idx_logs_record', 'record_id'),
        Index('idx_logs_type', 'request_type'),
    )


class HarmonyBaseline(db.Model):
    __tablename__ = 'harmony_baselines'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.Integer, default=1)
    tool_type = db.Column(db.String(50), nullable=False)
    style_tags = db.Column(db.Text)  # JSON array
    prompt_template = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=False)
    previous_id = db.Column(db.Integer, ForeignKey('harmony_baselines.id'), nullable=True)
    source_record_id = db.Column(db.Integer, ForeignKey('records.id'), nullable=True)
    rating = db.Column(db.Integer)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    previous = db.relationship('HarmonyBaseline', remote_side=[id],
                               backref='next_versions', foreign_keys=[previous_id])
    records_using = db.relationship('Record', foreign_keys='Record.baseline_id_used',
                                    back_populates='baseline')

    __table_args__ = (
        Index('idx_baselines_active', 'is_active'),
    )


class HermesSkill(db.Model):
    __tablename__ = 'hermes_skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    skill_name = db.Column(db.String(200), nullable=False)
    version = db.Column(db.String(20))
    source = db.Column(db.String(20), default='manual')  # manual|auto
    file_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    trigger_record_id = db.Column(db.Integer, ForeignKey('records.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DailyQuota(db.Model):
    __tablename__ = 'daily_quotas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False, unique=True, default=date.today)
    jimeng_total = db.Column(db.Integer, default=100)
    jimeng_used = db.Column(db.Integer, default=0)
    seedance_total = db.Column(db.Integer, default=130)
    seedance_used = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_quotas_date', 'date', unique=True),
    )
