"""actuator_execution_log

Revision ID: e76077ba625e
Revises: 5e4b7df306db
Create Date: 2026-11-10 18:09:01.608209

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e76077ba625e"
down_revision: str | Sequence[str] | None = "5e4b7df306db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "actuator_execution_log",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column(
            "policy_applied",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_actuator_execution_log_created_at",
        "actuator_execution_log",
        [sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix_actuator_execution_log_device_id",
        "actuator_execution_log",
        ["device_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_actuator_execution_log_device_id",
        table_name="actuator_execution_log",
    )
    op.drop_index(
        "ix_actuator_execution_log_created_at",
        table_name="actuator_execution_log",
    )
    op.drop_table("actuator_execution_log")
