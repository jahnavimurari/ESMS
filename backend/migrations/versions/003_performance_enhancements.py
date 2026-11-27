"""Performance enhancements: performance_cycles table, self_assessment, review lifecycle, and rating definitions

Revision ID: 003_performance_enhancements
Revises: 002_task_enhancements
Create Date: 2026-11-25 13:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_performance_enhancements'
down_revision = '002_task_enhancements'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create performance_cycles table
    op.create_table(
        'performance_cycles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('end_date >= start_date', name='chk_cycle_date_order'),
        sa.CheckConstraint('due_date >= start_date', name='chk_cycle_due_after_start'),
        sa.CheckConstraint("status IN ('ACTIVE', 'CLOSED')", name='chk_cycle_status'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Add columns to performance_reviews
    op.add_column('performance_reviews', sa.Column('cycle_id', sa.Integer(), nullable=True))
    op.add_column('performance_reviews', sa.Column('status', sa.String(length=25), server_default='DRAFT', nullable=False))
    op.add_column('performance_reviews', sa.Column('self_rating', sa.SmallInteger(), nullable=True))
    op.add_column('performance_reviews', sa.Column('accomplishments', sa.Text(), nullable=True))
    op.add_column('performance_reviews', sa.Column('challenges', sa.Text(), nullable=True))
    op.add_column('performance_reviews', sa.Column('skills_learned', sa.Text(), nullable=True))
    op.add_column('performance_reviews', sa.Column('development_plan', sa.Text(), nullable=True))
    op.add_column('performance_reviews', sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('performance_reviews', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))

    # 3. Alter existing columns in performance_reviews to be nullable (as self-assessment precedes manager review)
    bind = op.get_bind()
    if bind and bind.dialect.name == 'postgresql':
        op.alter_column('performance_reviews', 'rating', nullable=True)
        op.alter_column('performance_reviews', 'manager_feedback', nullable=True)
        op.alter_column('performance_reviews', 'reviewer_id', nullable=True)

        op.create_check_constraint(
            'chk_perf_self_rating_range',
            'performance_reviews',
            'self_rating IS NULL OR (self_rating >= 1 AND self_rating <= 5)'
        )
        op.create_check_constraint(
            'chk_perf_status',
            'performance_reviews',
            "status IN ('DRAFT', 'SELF_ASSESSMENT', 'MANAGER_REVIEW', 'COMPLETED', 'CANCELLED')"
        )

    # 4. Foreign key and unique constraint
    op.create_foreign_key(
        'fk_perf_cycle_id',
        'performance_reviews', 'performance_cycles',
        ['cycle_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_perf_emp_cycle', 'performance_reviews', ['employee_id', 'cycle_id'], unique=False)
    op.create_unique_constraint('uq_perf_emp_cycle', 'performance_reviews', ['employee_id', 'cycle_id'])


def downgrade():
    bind = op.get_bind()
    if bind and bind.dialect.name == 'postgresql':
        op.drop_constraint('chk_perf_status', 'performance_reviews', type_='check')
        op.drop_constraint('chk_perf_self_rating_range', 'performance_reviews', type_='check')

    op.drop_constraint('uq_perf_emp_cycle', 'performance_reviews', type_='unique')
    op.drop_index('idx_perf_emp_cycle', table_name='performance_reviews')
    op.drop_constraint('fk_perf_cycle_id', 'performance_reviews', type_='foreignkey')

    op.drop_column('performance_reviews', 'completed_at')
    op.drop_column('performance_reviews', 'submitted_at')
    op.drop_column('performance_reviews', 'development_plan')
    op.drop_column('performance_reviews', 'skills_learned')
    op.drop_column('performance_reviews', 'challenges')
    op.drop_column('performance_reviews', 'accomplishments')
    op.drop_column('performance_reviews', 'self_rating')
    op.drop_column('performance_reviews', 'status')
    op.drop_column('performance_reviews', 'cycle_id')

    op.drop_table('performance_cycles')

