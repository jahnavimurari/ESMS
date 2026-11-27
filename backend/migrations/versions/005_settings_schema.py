"""Phase 8: Settings and organization management schema

Revision ID: 005_settings_schema
Revises: 004_notifications_schema
Create Date: 2026-11-25 15:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_settings_schema'
down_revision = '004_notifications_schema'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Organization Settings
    op.create_table(
        'organization_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=150), server_default='ESMS Enterprise', nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('timezone', sa.String(length=50), server_default='UTC', nullable=False),
        sa.Column('date_format', sa.String(length=30), server_default='YYYY-MM-DD', nullable=False),
        sa.Column('time_format', sa.String(length=20), server_default='24H', nullable=False),
        sa.Column('working_days', sa.String(length=100), server_default='MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY', nullable=False),
        sa.Column('daily_working_hours', sa.Numeric(precision=4, scale=2), server_default='8.00', nullable=False),
        sa.Column('fiscal_year_start_month', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Designations
    op.create_table(
        'designations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_designation_name'),
        sa.UniqueConstraint('code', name='uq_designation_code')
    )
    op.create_index('idx_designations_code', 'designations', ['code'])
    op.create_index('idx_designations_dept', 'designations', ['department_id'])

    # 3. Holidays
    op.create_table(
        'holidays',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('holiday_date', sa.Date(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('is_optional', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('holiday_date', name='uq_holiday_date')
    )
    op.create_index('idx_holidays_year', 'holidays', ['year'])
    op.create_index('idx_holidays_date', 'holidays', ['holiday_date'])

    # 4. Work Shifts
    op.create_table(
        'work_shifts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('start_time', sa.String(length=10), server_default='09:00', nullable=False),
        sa.Column('end_time', sa.String(length=10), server_default='18:00', nullable=False),
        sa.Column('grace_period_minutes', sa.Integer(), server_default='15', nullable=False),
        sa.Column('half_day_hours', sa.Numeric(precision=4, scale=2), server_default='4.00', nullable=False),
        sa.Column('full_day_hours', sa.Numeric(precision=4, scale=2), server_default='8.00', nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_shift_name'),
        sa.UniqueConstraint('code', name='uq_shift_code')
    )

    # 5. Employee Categories
    op.create_table(
        'employee_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_emp_cat_code')
    )

    # 6. User Preferences
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email_notifications', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('in_app_notifications', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('theme', sa.String(length=20), server_default='LIGHT', nullable=False),
        sa.Column('date_format', sa.String(length=30), server_default='YYYY-MM-DD', nullable=False),
        sa.Column('time_format', sa.String(length=20), server_default='24H', nullable=False),
        sa.Column('dashboard_layout', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_preference_user')
    )


def downgrade():
    op.drop_table('user_preferences')
    op.drop_table('employee_categories')
    op.drop_table('work_shifts')
    op.drop_index('idx_holidays_date', table_name='holidays')
    op.drop_index('idx_holidays_year', table_name='holidays')
    op.drop_table('holidays')
    op.drop_index('idx_designations_dept', table_name='designations')
    op.drop_index('idx_designations_code', table_name='designations')
    op.drop_table('designations')
    op.drop_table('organization_settings')

