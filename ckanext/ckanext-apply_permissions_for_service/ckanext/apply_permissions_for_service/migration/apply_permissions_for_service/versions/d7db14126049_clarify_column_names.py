"""clarify column names

Revision ID: d7db14126049
Revises: 13981b4847ac
Create Date: 2023-01-13 14:49:51.270751

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd7db14126049'
down_revision = '13981b4847ac'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('apply_permission', 'subsystem_id', new_column_name='target_subsystem_id')
    op.alter_column('apply_permission', 'subsystem_code', new_column_name='subsystem_id')
    op.alter_column('apply_permission', 'business_code', new_column_name='member_code')
    op.alter_column('apply_permission', 'intermediate_business_code', new_column_name='intermediate_member_code')
    op.alter_column('apply_permission', 'service_code_list', new_column_name='service_id_list')


def downgrade():
    op.alter_column('apply_permission', 'subsystem_id', new_column_name='subsystem_code')
    op.alter_column('apply_permission', 'target_subsystem_id', new_column_name='subsystem_id')
    op.alter_column('apply_permission', 'member_code', new_column_name='business_code')
    op.alter_column('apply_permission', 'intermediate_member_code', new_column_name='intermediate_business_code')
    op.alter_column('apply_permission', 'service_id_list', new_column_name='service_code_list')
