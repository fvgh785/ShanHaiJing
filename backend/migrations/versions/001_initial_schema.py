"""Initial schema: plans, records, hermes_logs, harmony_baselines, hermes_skills, daily_quotas

Revision ID: 001_initial
Revises: None
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(name):
    conn = op.get_bind()
    return name in inspect(conn).get_table_names()


def upgrade():
    if not _table_exists('plans'):
        op.create_table('plans',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('creature', sa.String(100), nullable=False),
            sa.Column('juan', sa.String(50)),
            sa.Column('priority', sa.Integer(), server_default='3'),
            sa.Column('planned_date', sa.Date(), nullable=False),
            sa.Column('recommended_tool', sa.String(100)),
            sa.Column('status', sa.String(20), server_default='pending'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp()),
            sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.current_timestamp()),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('idx_plans_status_date', 'plans', ['status', 'planned_date'])

    if not _table_exists('harmony_baselines'):
        op.create_table('harmony_baselines',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('version', sa.Integer(), server_default='1'),
            sa.Column('tool_type', sa.String(50), nullable=False),
            sa.Column('style_tags', sa.Text()),
            sa.Column('prompt_template', sa.Text(), nullable=False),
            sa.Column('file_path', sa.String(500)),
            sa.Column('is_active', sa.Boolean(), server_default='0'),
            sa.Column('previous_id', sa.Integer(), sa.ForeignKey('harmony_baselines.id'), nullable=True),
            sa.Column('source_record_id', sa.Integer(), nullable=True),
            sa.Column('rating', sa.Integer()),
            sa.Column('usage_count', sa.Integer(), server_default='0'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp()),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('idx_baselines_active', 'harmony_baselines', ['is_active'])

    if not _table_exists('daily_quotas'):
        op.create_table('daily_quotas',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('jimeng_total', sa.Integer(), server_default='100'),
            sa.Column('jimeng_used', sa.Integer(), server_default='0'),
            sa.Column('seedance_total', sa.Integer(), server_default='130'),
            sa.Column('seedance_used', sa.Integer(), server_default='0'),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp()),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('date'),
        )
        op.create_index('idx_quotas_date', 'daily_quotas', ['date'], unique=True)

    if not _table_exists('records'):
        op.create_table('records',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('plan_id', sa.Integer(), sa.ForeignKey('plans.id'), nullable=True),
            sa.Column('work_date', sa.Date(), nullable=False),
            sa.Column('creature_name', sa.String(100), nullable=False),
            sa.Column('tools_used', sa.Text()),
            sa.Column('baseline_id_used', sa.Integer(), sa.ForeignKey('harmony_baselines.id'), nullable=True),
            sa.Column('prompt_image', sa.Text()),
            sa.Column('prompt_video', sa.Text()),
            sa.Column('negative_prompt', sa.Text()),
            sa.Column('style_review_score', sa.Float()),
            sa.Column('style_review_suggestions', sa.Text()),
            sa.Column('points_consumed', sa.Integer()),
            sa.Column('output_url', sa.Text()),
            sa.Column('intermediate_urls', sa.Text()),
            sa.Column('notes', sa.Text()),
            sa.Column('status', sa.String(20), server_default='in_progress'),
            sa.Column('hermes_skill_version', sa.String(50)),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp()),
            sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.current_timestamp()),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('idx_records_creature', 'records', ['creature_name'])
        op.create_index('idx_records_date', 'records', ['work_date'])
        op.create_index('idx_records_status', 'records', ['status'])

    # FK harmony_baselines.source_record_id → records.id.
    # Only possible when both tables are created fresh in this run;
    # SQLite cannot ALTER existing tables to add constraints. If
    # harmony_baselines survived a prior partial migration, the FK
    # is left missing (the ORM relationship still works without it).
    if not _table_exists('harmony_baselines') and not _table_exists('records'):
        op.create_foreign_key(
            'fk_harmony_baselines_source_record_id',
            'harmony_baselines', 'records',
            ['source_record_id'], ['id']
        )

    if not _table_exists('hermes_logs'):
        op.create_table('hermes_logs',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('record_id', sa.Integer(), sa.ForeignKey('records.id'), nullable=True),
            sa.Column('request_type', sa.String(30), nullable=False),
            sa.Column('system_prompt', sa.Text()),
            sa.Column('user_input', sa.Text()),
            sa.Column('response_body', sa.Text()),
            sa.Column('baseline_id_used', sa.Integer(), sa.ForeignKey('harmony_baselines.id'), nullable=True),
            sa.Column('tokens_input', sa.Integer()),
            sa.Column('tokens_output', sa.Integer()),
            sa.Column('api_cost', sa.Float()),
            sa.Column('duration_ms', sa.Integer()),
            sa.Column('adopted', sa.Boolean(), server_default='0'),
            sa.Column('user_edited', sa.Boolean(), server_default='0'),
            sa.Column('error_message', sa.Text()),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp()),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('idx_logs_record', 'hermes_logs', ['record_id'])
        op.create_index('idx_logs_type', 'hermes_logs', ['request_type'])

    if not _table_exists('hermes_skills'):
        op.create_table('hermes_skills',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('skill_name', sa.String(200), nullable=False),
            sa.Column('version', sa.String(20)),
            sa.Column('source', sa.String(20), server_default='manual'),
            sa.Column('file_path', sa.String(500), nullable=False),
            sa.Column('description', sa.Text()),
            sa.Column('trigger_record_id', sa.Integer(), sa.ForeignKey('records.id'), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='1'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp()),
            sa.PrimaryKeyConstraint('id'),
        )

    op.execute('PRAGMA journal_mode=WAL')


def downgrade():
    op.drop_table('hermes_skills')
    op.drop_table('hermes_logs')
    op.execute('PRAGMA journal_mode=DELETE')
    op.drop_constraint('fk_harmony_baselines_source_record_id', 'harmony_baselines', type_='foreignkey')
    op.drop_table('records')
    op.drop_table('daily_quotas')
    op.drop_table('harmony_baselines')
    op.drop_table('plans')
