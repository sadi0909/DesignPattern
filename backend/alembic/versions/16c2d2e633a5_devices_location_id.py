"""devices_location_id

Revision ID: 16c2d2e633a5
Revises: e76077ba625e
Create Date: 2026-11-17 15:10:26.765449

Activate the optional nullable devices.location_id link first allowed by the
Phase 3 handoff and Phase 4 Builder schema. This is an earlier-phase extension,
not a new Phase 7 business table.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "16c2d2e633a5"
down_revision: str | Sequence[str] | None = "e76077ba625e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("devices", sa.Column("location_id", sa.UUID(), nullable=True))
    op.create_index("ix_devices_location_id", "devices", ["location_id"], unique=False)
    op.create_foreign_key(
        "fk_devices_location_id_locations",
        "devices",
        "locations",
        ["location_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_devices_location_id_locations",
        "devices",
        type_="foreignkey",
    )
    op.drop_index("ix_devices_location_id", table_name="devices")
    op.drop_column("devices", "location_id")
