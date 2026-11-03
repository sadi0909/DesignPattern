"""actuator_states

Revision ID: 5e4b7df306db
Revises: a1c3e9f07b2d
Create Date: 2026-11-03 18:00:35

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5e4b7df306db"
down_revision: str | Sequence[str] | None = "a1c3e9f07b2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "actuator_states",
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("device_id"),
    )
    # Seed every actuator that already exists. New actuators get an idle row
    # from DeviceRepository.save_devices in the same transaction.
    op.execute(
        """
        INSERT INTO actuator_states (device_id, state, updated_at)
        SELECT id, 'idle', now() FROM devices WHERE role = 'actuator'
        ON CONFLICT (device_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("actuator_states")
