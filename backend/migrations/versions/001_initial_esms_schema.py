"""Initial ESMS relational database schema

Revision ID: 001_initial_esms_schema
Revises: 
Create Date: 2026-11-25 11:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_esms_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 0. Enable btree_gist extension for PostgreSQL exclusion constraints
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), server_default='EMPLOYEE', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('ADMIN', 'HR', 'EMPLOYEE')", name='chk_user_role'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_role', 'users', ['role'], unique=False)

    # 2. revoked_tokens table
    op.create_table(
        'revoked_tokens',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('jti', sa.String(length=36), nullable=False),
        sa.Column('token_type', sa.String(length=10), server_default='access', nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti')
    )
    op.create_index('idx_revoked_tokens_jti', 'revoked_tokens', ['jti'], unique=True)
    op.create_index('idx_revoked_tokens_expires', 'revoked_tokens', ['expires_at'], unique=False)

    # 3. departments table
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_departments_name', 'departments', ['name'], unique=True)
    op.create_index('idx_departments_code', 'departments', ['code'], unique=True)

    # 4. employees table
    op.create_table(
        'employees',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_code', sa.String(length=30), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('designation', sa.String(length=100), nullable=False),
        sa.Column('joining_date', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
        sa.Column('employment_type', sa.String(length=30), server_default='FULL_TIME', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='ACTIVE', nullable=False),
        sa.Column('reporting_manager_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('profile_image_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint("gender IN ('MALE', 'FEMALE', 'OTHER', 'PREFER_NOT_TO_SAY')", name='chk_emp_gender'),
        sa.CheckConstraint("employment_type IN ('FULL_TIME', 'PART_TIME', 'CONTRACT', 'INTERN')", name='chk_emp_type'),
        sa.CheckConstraint("status IN ('ACTIVE', 'ON_LEAVE', 'TERMINATED', 'SUSPENDED')", name='chk_emp_status'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['reporting_manager_id'], ['employees.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_code'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_employees_code', 'employees', ['employee_code'], unique=True)
    op.create_index('idx_employees_dept', 'employees', ['department_id'], unique=False)
    op.create_index('idx_employees_manager', 'employees', ['reporting_manager_id'], unique=False)
    op.create_index('idx_employees_names', 'employees', ['first_name', 'last_name'], unique=False)

    # 5. attendance table (Multi-shift & concurrency protected)
    op.create_table(
        'attendance',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('work_date', sa.Date(), nullable=False),
        sa.Column('shift_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('check_in', sa.DateTime(timezone=True), nullable=False),
        sa.Column('check_out', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_hours', sa.Numeric(precision=4, scale=2), server_default='0.00', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='PRESENT', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_corrected', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('corrected_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint("status IN ('PRESENT', 'LATE', 'HALF_DAY', 'ABSENT')", name='chk_att_status'),
        sa.CheckConstraint('check_out IS NULL OR check_out > check_in', name='chk_att_checkout_after_checkin'),
        sa.CheckConstraint('total_hours >= 0 AND total_hours <= 24', name='chk_att_hours_range'),
        sa.CheckConstraint('shift_number >= 1', name='chk_att_shift_number'),
        sa.ForeignKeyConstraint(['corrected_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id', 'work_date', 'shift_number', name='uq_att_emp_date_shift')
    )
    op.create_index('idx_attendance_emp_date', 'attendance', ['employee_id', 'work_date'], unique=False)
    # Partial unique index: Only 1 active check-in session per employee (where check_out is NULL)
    op.create_index(
        'uq_att_active_session',
        'attendance',
        ['employee_id'],
        unique=True,
        postgresql_where=sa.text('check_out IS NULL')
    )

    # 6. leave_types table
    op.create_table(
        'leave_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('days_per_year', sa.Integer(), server_default='12', nullable=False),
        sa.Column('is_paid', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

    # 7. leave_requests table with range overlap exclusion constraint
    op.create_table(
        'leave_requests',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('leave_type_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('total_days', sa.Numeric(precision=4, scale=1), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='PENDING', nullable=False),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewer_comments', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint("status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')", name='chk_leave_status'),
        sa.CheckConstraint('end_date >= start_date', name='chk_leave_date_order'),
        sa.CheckConstraint('total_days > 0', name='chk_leave_positive_days'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['leave_type_id'], ['leave_types.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_leave_dates', 'leave_requests', ['start_date', 'end_date'], unique=False)
    op.create_index('idx_leave_emp_status', 'leave_requests', ['employee_id', 'status'], unique=False)
    
    # PostgreSQL Exclusion Constraint using GiST with btree_gist:
    # Physically prevents any concurrent overlapping PENDING or APPROVED leave requests for the same employee
    op.execute("""
        ALTER TABLE leave_requests
        ADD CONSTRAINT uq_leave_no_overlap
        EXCLUDE USING gist (
            employee_id WITH =,
            daterange(start_date, end_date, '[]') WITH &&
        )
        WHERE (status IN ('PENDING', 'APPROVED'));
    """)

    # 8. tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('priority', sa.String(length=20), server_default='MEDIUM', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='TODO', nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint("priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')", name='chk_task_priority'),
        sa.CheckConstraint("status IN ('TODO', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED')", name='chk_task_status'),
        sa.ForeignKeyConstraint(['assigned_to'], ['employees.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tasks_assignee_status', 'tasks', ['assigned_to', 'status'], unique=False)
    op.create_index('idx_tasks_due_date', 'tasks', ['due_date'], unique=False)

    # 9. performance_reviews table
    op.create_table(
        'performance_reviews',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('review_period', sa.String(length=50), nullable=False),
        sa.Column('rating', sa.SmallInteger(), nullable=False),
        sa.Column('goals_achievement', sa.Text(), nullable=True),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('areas_for_improvement', sa.Text(), nullable=True),
        sa.Column('manager_feedback', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='chk_perf_rating_range'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_perf_emp_period', 'performance_reviews', ['employee_id', 'review_period'], unique=False)

    # 10. audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_entity', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.String(length=100), nullable=True),
        sa.Column('previous_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_entity', 'audit_logs', ['target_entity', 'target_id'], unique=False)
    op.create_index('idx_audit_timestamp_desc', 'audit_logs', [sa.text('timestamp DESC')], unique=False)


def downgrade():
    op.drop_table('audit_logs')
    op.drop_table('performance_reviews')
    op.drop_table('tasks')
    op.drop_table('leave_requests')
    op.drop_table('leave_types')
    op.drop_table('attendance')
    op.drop_table('employees')
    op.drop_table('departments')
    op.drop_table('revoked_tokens')
    op.drop_table('users')

