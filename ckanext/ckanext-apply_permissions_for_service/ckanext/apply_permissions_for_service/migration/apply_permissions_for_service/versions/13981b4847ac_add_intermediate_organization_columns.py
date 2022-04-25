"""Add intermediate organization columns

Revision ID: 13981b4847ac
Revises: e7cd24026024
Create Date: 2022-04-21 13:08:26.718811

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13981b4847ac'
down_revision = 'e7cd24026024'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('apply_permission', sa.Column('intermediate_organization_id', sa.String(255), nullable=True))
    op.add_column('apply_permission', sa.Column('intermediate_business_code', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('apply_permission', 'intermediate_organization_id')
    op.drop_column('apply_permission', 'intermediate_business_code')
