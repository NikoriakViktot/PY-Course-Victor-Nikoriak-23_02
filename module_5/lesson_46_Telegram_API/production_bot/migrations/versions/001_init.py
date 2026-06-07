"""init

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tg_id", sa.BigInteger(), unique=True, nullable=False, index=True),
        sa.Column("username", sa.String(64)),
        sa.Column("first_name", sa.String(128), nullable=False),
        sa.Column("last_name", sa.String(128)),
        sa.Column("language_code", sa.String(8)),
        sa.Column("is_blocked", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_admin", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), unique=True, index=True),
        sa.Column("tier", sa.String(16), default="free", nullable=False),
        sa.Column("requests_limit", sa.Integer(), default=10, nullable=False),
        sa.Column("requests_used", sa.Integer(), default=0, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(8), default="XTR", nullable=False),
        sa.Column("status", sa.String(16), default="pending", nullable=False),
        sa.Column("telegram_payment_charge_id", sa.String(256)),
        sa.Column("subscription_tier", sa.String(16)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("content_type", sa.String(32), nullable=False),
        sa.Column("text", sa.Text()),
        sa.Column("command", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )
    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("referrer_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
        sa.Column("referred_id", sa.Integer(), sa.ForeignKey("users.id"), unique=True),
        sa.Column("bonus_granted", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_username", sa.String(64), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("target_user_id", sa.BigInteger()),
        sa.Column("details", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("referrals")
    op.drop_table("messages")
    op.drop_table("payments")
    op.drop_table("subscriptions")
    op.drop_table("users")
