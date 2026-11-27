"""Phase 9: Security and administration schema

Revision ID: 006_security_admin_schema
Revises: 005_settings_schema
Create Date: 2026-11-25 17:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_security_admin_schema'
down_revision = '005_settings_schema'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pwd_reset_user', 'password_reset_tokens', ['user_id'])
    op.create_index('idx_pwd_reset_hash', 'password_reset_tokens', ['token_hash'])
    op.create_index('idx_pwd_reset_exp', 'password_reset_tokens', ['expires_at'])


def downgrade():
    op.drop_index('idx_pwd_reset_exp', table_name='password_reset_tokens')
    op.drop_index('idx_pwd_reset_hash', table_name='password_reset_tokens')
    op.drop_index('idx_pwd_reset_user', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')

