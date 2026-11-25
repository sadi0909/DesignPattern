"""schema hardening

Revision ID: b7d4c2a91f30
Revises: 0f8f495c39ee
Create Date: 2026-11-24 22:00:00.000000

Phase 12 forward-only hardening: replace the single-column alert indexes with
composite indexes that match the feed queries (`status` or `location_id`, then
newest `created_at`). Foreign keys already carry their ON DELETE policies from
the revisions that introduced each table; none are rewritten here.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d4c2a91f30"
down_revision: str | Sequence[str] | None = "0f8f495c39ee"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_alerts_status_created_at",
        "alerts",
        ["status", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix_alerts_location_id_created_at",
        "alerts",
        ["location_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_index("ix_alerts_location_id", table_name="alerts")


def downgrade() -> None:
    op.create_index("ix_alerts_location_id", "alerts", ["location_id"], unique=False)
    op.create_index("ix_alerts_status", "alerts", ["status"], unique=False)
    op.drop_index("ix_alerts_location_id_created_at", table_name="alerts")
    op.drop_index("ix_alerts_status_created_at", table_name="alerts")
