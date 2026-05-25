"""add manual escalation fields

Revision ID: 20240115_manual_esc
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20240115_manual_esc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add manual_reason to escalations
    op.add_column('escalations', sa.Column('manual_reason', sa.String(length=500), nullable=True))
    op.add_column('escalations', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))
    
    # 2. Add subject_area to users (Needed for assignment logic)
    op.add_column('users', sa.Column('subject_area', sa.String(), nullable=True))

    # 3. Update enums
    # We use execute for raw SQL as requested
    op.execute("ALTER TYPE escalation_trigger_reason_enum ADD VALUE IF NOT EXISTS 'manual_request'")
    op.execute("ALTER TYPE escalation_status_enum ADD VALUE IF NOT EXISTS 'cancelled'")


def downgrade():
    op.drop_column('users', 'subject_area')
    op.drop_column('escalations', 'resolved_at')
    op.drop_column('escalations', 'manual_reason')
    # Note: Removing enum values in Postgres is complex and often not recommended in migrations
