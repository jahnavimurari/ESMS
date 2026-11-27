"""Task enhancements: start_date, category, department_id, and extended status lifecycle

Revision ID: 002_task_enhancements
Revises: 001_initial_esms_schema
Create Date: 2026-11-25 13:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_task_enhancements'
down_revision = '001_initial_esms_schema'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add category and start_date columns
    op.add_column('tasks', sa.Column('category', sa.String(length=50), nullable=True))
    op.add_column('tasks', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('tasks', sa.Column('department_id', sa.Integer(), nullable=True))

    # 2. Add foreign key for department_id
    op.create_foreign_key(
        'fk_tasks_department_id',
        'tasks', 'departments',
        ['department_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_tasks_dept', 'tasks', ['department_id'], unique=False)

    # 3. Update status constraint to include REVIEW and CANCELLED
    bind = op.get_bind()
    if bind and bind.dialect.name == 'postgresql':
        op.drop_constraint('chk_task_status', 'tasks', type_='check')
        op.create_check_constraint(
            'chk_task_status',
            'tasks',
            "status IN ('TODO', 'IN_PROGRESS', 'REVIEW', 'COMPLETED', 'BLOCKED', 'CANCELLED')"
        )
        op.create_check_constraint(
            'chk_task_date_order',
            'tasks',
            "due_date IS NULL OR start_date IS NULL OR due_date >= start_date"
        )


def downgrade():
    bind = op.get_bind()
    if bind and bind.dialect.name == 'postgresql':
        op.drop_constraint('chk_task_date_order', 'tasks', type_='check')
        op.drop_constraint('chk_task_status', 'tasks', type_='check')
        op.create_check_constraint(
            'chk_task_status',
            'tasks',
            "status IN ('TODO', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED')"
        )

    op.drop_index('idx_tasks_dept', table_name='tasks')
    op.drop_constraint('fk_tasks_department_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'department_id')
    op.drop_column('tasks', 'start_date')
    op.drop_column('tasks', 'category')

