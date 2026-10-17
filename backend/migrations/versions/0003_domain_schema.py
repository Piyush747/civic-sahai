"""align the database with the application models

Creates the users, cities, landmarks, images, incidents, and resource tables
that seed and the clustering worker already use. Also finishes zones and
complaints, including the unique complaint link that keeps clustering idempotent.
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_domain_schema"
down_revision = "0002_complaint_landmark"
branch_labels = None
depends_on = None


def _timestamp(name: str) -> sa.Column:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


def upgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT COUNT(*) FROM zones")).scalar_one():
        raise RuntimeError(
            "zones already has rows and no city_id. Create a new database, "
            "run alembic upgrade head, then seed it."
        )

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("initials", sa.String(8), nullable=False),
        sa.Column("user_type", sa.String(32), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        _timestamp("created_at"),
    )
    op.create_index("ix_users_user_type", "users", ["user_type"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "cities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("admin_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        _timestamp("created_at"),
    )
    op.create_index("ix_cities_admin_user_id", "cities", ["admin_user_id"])

    with op.batch_alter_table("zones") as batch:
        batch.add_column(sa.Column("city_id", sa.String(36), nullable=False))
        batch.add_column(sa.Column("boundary", sa.JSON(), nullable=True))
        batch.create_foreign_key("zones_city_id_fkey", "cities", ["city_id"], ["id"])
        batch.create_unique_constraint("uq_zones_city_id_id", ["city_id", "id"])
        batch.create_index("ix_zones_city_id", ["city_id"])

    with op.batch_alter_table("complaints") as batch:
        batch.alter_column(
            "user_id",
            existing_type=sa.String(120),
            type_=sa.String(36),
            nullable=False,
        )
        batch.create_foreign_key("complaints_user_id_fkey", "users", ["user_id"], ["id"])
        batch.create_check_constraint(
            "ck_complaints_status",
            "status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')",
        )
        batch.create_index("ix_complaints_user_created_at", ["user_id", "created_at"])
        batch.create_index("ix_complaints_zone_status", ["zone_id", "status"])

    op.create_table(
        "landmarks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("zone_id", sa.String(64), sa.ForeignKey("zones.id"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("landmark_type", sa.String(64), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("criticality_weight", sa.Float(), nullable=False),
        _timestamp("created_at"),
        sa.CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="ck_landmarks_latitude",
        ),
        sa.CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_landmarks_longitude",
        ),
        sa.CheckConstraint(
            "criticality_weight >= 0",
            name="ck_landmarks_criticality_weight",
        ),
    )
    op.create_index("ix_landmarks_zone_id", "landmarks", ["zone_id"])
    op.create_index("ix_landmarks_landmark_type", "landmarks", ["landmark_type"])

    op.create_table(
        "complaint_images",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "complaint_id",
            sa.String(36),
            sa.ForeignKey("complaints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("image_id", sa.String(255), nullable=False),
        _timestamp("created_at"),
    )
    op.create_index("ix_complaint_images_complaint_id", "complaint_images", ["complaint_id"])

    op.create_table(
        "incidents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("city_id", sa.String(36), nullable=False),
        sa.Column("zone_id", sa.String(64), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=True),
        sa.Column("priority_version", sa.String(64), nullable=True),
        sa.Column("priority_metadata", sa.JSON(), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.ForeignKeyConstraint(
            ["city_id", "zone_id"],
            ["zones.city_id", "zones.id"],
            name="fk_incidents_city_zone",
        ),
        sa.CheckConstraint(
            "status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')",
            name="ck_incidents_status",
        ),
    )
    op.create_index("ix_incidents_category", "incidents", ["category"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_priority", "incidents", ["priority_score"])
    op.create_index("ix_incidents_created_at", "incidents", ["created_at"])
    op.create_index("ix_incidents_city_status", "incidents", ["city_id", "status"])

    op.create_table(
        "incident_complaints",
        sa.Column(
            "incident_id",
            sa.String(36),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "complaint_id",
            sa.String(36),
            sa.ForeignKey("complaints.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("relationship_type", sa.String(32), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("matched_by", sa.String(32), nullable=False),
        _timestamp("matched_at"),
        sa.UniqueConstraint("complaint_id", name="uq_incident_complaints_complaint_id"),
        sa.CheckConstraint(
            "relationship_type IN ('PRIMARY', 'DUPLICATE')",
            name="ck_incident_complaints_relationship_type",
        ),
        sa.CheckConstraint(
            "match_score IS NULL OR (match_score >= 0 AND match_score <= 1)",
            name="ck_incident_complaints_match_score",
        ),
    )
    op.create_index(
        "ix_incident_complaints_complaint_id",
        "incident_complaints",
        ["complaint_id"],
    )

    op.create_table(
        "resource_types",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
    )

    op.create_table(
        "zone_resources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("zone_id", sa.String(64), sa.ForeignKey("zones.id"), nullable=False),
        sa.Column(
            "resource_type_id",
            sa.String(36),
            sa.ForeignKey("resource_types.id"),
            nullable=False,
        ),
        sa.Column("initial_capacity", sa.Float(), nullable=False),
        sa.Column("available_capacity", sa.Float(), nullable=False),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.UniqueConstraint("zone_id", "resource_type_id", name="uq_zone_resources_zone_type"),
        sa.CheckConstraint("initial_capacity >= 0", name="ck_zone_resources_initial_capacity"),
        sa.CheckConstraint(
            "available_capacity >= 0 AND available_capacity <= initial_capacity",
            name="ck_zone_resources_available_capacity",
        ),
    )
    op.create_index("ix_zone_resources_resource_type_id", "zone_resources", ["resource_type_id"])

    op.create_table(
        "incident_resource_requirements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "incident_id",
            sa.String(36),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "resource_type_id",
            sa.String(36),
            sa.ForeignKey("resource_types.id"),
            nullable=False,
        ),
        sa.Column("required_quantity", sa.Float(), nullable=False),
        sa.Column("allocated_quantity", sa.Float(), nullable=False),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.UniqueConstraint(
            "incident_id",
            "resource_type_id",
            name="uq_incident_requirements_incident_type",
        ),
        sa.CheckConstraint(
            "required_quantity >= 0",
            name="ck_incident_requirements_required_quantity",
        ),
        sa.CheckConstraint(
            "allocated_quantity >= 0 AND allocated_quantity <= required_quantity",
            name="ck_incident_requirements_allocated_quantity",
        ),
    )
    op.create_index(
        "ix_incident_resource_requirements_incident_id",
        "incident_resource_requirements",
        ["incident_id"],
    )
    op.create_index(
        "ix_incident_resource_requirements_resource_type_id",
        "incident_resource_requirements",
        ["resource_type_id"],
    )

    op.create_table(
        "resource_allocations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("source_zone_id", sa.String(64), sa.ForeignKey("zones.id"), nullable=False),
        sa.Column(
            "resource_type_id",
            sa.String(36),
            sa.ForeignKey("resource_types.id"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.CheckConstraint("quantity > 0", name="ck_resource_allocations_quantity"),
        sa.CheckConstraint(
            "status IN ('PROPOSED', 'COMMITTED', 'RELEASED', 'CANCELLED')",
            name="ck_resource_allocations_status",
        ),
    )
    op.create_index(
        "ix_resource_allocations_incident_status",
        "resource_allocations",
        ["incident_id", "status"],
    )
    op.create_index(
        "ix_resource_allocations_source_zone_id",
        "resource_allocations",
        ["source_zone_id"],
    )


def downgrade() -> None:
    op.drop_table("resource_allocations")
    op.drop_table("incident_resource_requirements")
    op.drop_table("zone_resources")
    op.drop_table("resource_types")
    op.drop_table("incident_complaints")
    op.drop_table("incidents")
    op.drop_table("complaint_images")
    op.drop_table("landmarks")
    with op.batch_alter_table("complaints") as batch:
        batch.drop_index("ix_complaints_zone_status")
        batch.drop_index("ix_complaints_user_created_at")
        batch.drop_constraint("ck_complaints_status", type_="check")
        batch.drop_constraint("complaints_user_id_fkey", type_="foreignkey")
        batch.alter_column(
            "user_id",
            existing_type=sa.String(36),
            type_=sa.String(120),
            nullable=True,
        )
    with op.batch_alter_table("zones") as batch:
        batch.drop_index("ix_zones_city_id")
        batch.drop_constraint("uq_zones_city_id_id", type_="unique")
        batch.drop_constraint("zones_city_id_fkey", type_="foreignkey")
        batch.drop_column("boundary")
        batch.drop_column("city_id")
    op.drop_table("cities")
    op.drop_table("users")
