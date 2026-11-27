"""Phase 7: Notifications and announcements schema

Revision ID: 004_notifications_schema
Revises: 003_performance_enhancements
Create Date: 2026-11-25 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_notifications_schema'
down_revision = '003_performance_enhancements'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'notifications',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), server_default='SYSTEM', nullable=False),
        sa.Column('priority', sa.String(length=20), server_default='NORMAL', nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('action_url', sa.String(length=255), nullable=True),
        sa.Column('meta_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint(
            "category IN ('ATTENDANCE', 'LEAVE', 'TASK', 'PERFORMANCE', 'SYSTEM', 'ANNOUNCEMENT')",
            name='chk_notif_category'
        ),
        sa.CheckConstraint(
            "priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')",
            name='chk_notif_priority'
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notif_user_unread', 'notifications', ['user_id', 'is_read'])
    op.create_index('idx_notif_user_created', 'notifications', ['user_id', 'created_at'])


def downgrade():
    op.drop_index('idx_notif_user_created', table_name='notifications')
    op.drop_index('idx_notif_user_unread', table_name='notifications')
    op.drop_table('notifications')

