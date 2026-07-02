"""Create lead table.

Revision ID: 20260702_01
Revises:
Create Date: 2026-07-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260702_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'lead',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('public_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('organization', sa.String(255), nullable=True),
        sa.Column('role_title', sa.String(100), nullable=True),
        sa.Column('school_size', sa.String(50), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='new'),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_id'),
        schema='leads'
    )
    op.create_index('ix_leads_email', 'lead', ['email'], schema='leads')
    op.create_index('ix_leads_status', 'lead', ['status'], schema='leads')
    op.create_index('ix_leads_created_at', 'lead', ['created_at'], schema='leads')


def downgrade() -> None:
    op.drop_index('ix_leads_created_at', table_name='lead', schema='leads')
    op.drop_index('ix_leads_status', table_name='lead', schema='leads')
    op.drop_index('ix_leads_email', table_name='lead', schema='leads')
    op.drop_table('lead', schema='leads')
