"""initial civic complaint schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("zones", sa.Column("id", sa.String(64), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("population", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("complaints", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(120)), sa.Column("title", sa.String(160), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("category", sa.String(32), nullable=False), sa.Column("latitude", sa.Float(), nullable=False), sa.Column("longitude", sa.Float(), nullable=False), sa.Column("address", sa.String(255), nullable=False), sa.Column("zone_id", sa.String(64), sa.ForeignKey("zones.id"), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("priority_score", sa.Float()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    for column in ("user_id", "category", "zone_id", "status", "created_at"):
        op.create_index(f"ix_complaints_{column}", "complaints", [column])

def downgrade() -> None:
    op.drop_table("complaints")
    op.drop_table("zones")

