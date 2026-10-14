"""store an optional complaint landmark"""
from alembic import op
import sqlalchemy as sa

revision = "0002_complaint_landmark"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("complaints") as batch:
        batch.add_column(sa.Column("landmark", sa.String(160), nullable=True))
        batch.alter_column("address", type_=sa.String(300), existing_type=sa.String(255))


def downgrade() -> None:
    with op.batch_alter_table("complaints") as batch:
        batch.drop_column("landmark")
        batch.alter_column("address", type_=sa.String(255), existing_type=sa.String(300))
