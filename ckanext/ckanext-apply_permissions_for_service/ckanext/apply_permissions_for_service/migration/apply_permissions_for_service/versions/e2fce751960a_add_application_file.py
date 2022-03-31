"""Add application file

Revision ID: e2fce751960a
Revises: 
Create Date: 2022-03-30 09:36:38.997096

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2fce751960a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('apply_permission', sa.Column('application_filename', sa.String(255), nullable=True))
    pass


def downgrade():
    op.drop_column('apply_permission', 'application_filename')
    pass
