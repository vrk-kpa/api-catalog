"""Add application file

Revision ID: e2fdr852000b
Revises:
Create Date: 2022-04-08 11:45:38.997096

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2fdr852000b'
down_revision = 'e2fce751960a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('apply_permission', sa.Column('intermediate_organization_id', sa.String(255), nullable=True))
    op.add_column('apply_permission', sa.Column('intermediate_business_code', sa.String(255), nullable=True))
    pass


def downgrade():
    op.drop_column('apply_permission', 'intermediate_organization_id')
    op.drop_column('apply_permission', 'intermediate_business_code')
    pass
