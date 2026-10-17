"""Remove obsolete resource-allocation schema."""
import sqlalchemy as sa
from alembic import op

revision = "0004_remove_resource_allocation"
down_revision = "0003_domain_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = set(inspector.get_table_names())
    for table in (
        "incident_assignments",
        "allocation_recommendations",
        "resource_allocations",
        "incident_resource_requirements",
        "zone_resources",
        "resource_types",
        "teams",
    ):
        if table in existing:
            op.drop_table(table)


def downgrade() -> None:
    # The removed tables are intentionally not recreated because their data
    # cannot be recovered. A downgrade continues through the historical
    # migrations, which remove the schema they originally created.
    pass
