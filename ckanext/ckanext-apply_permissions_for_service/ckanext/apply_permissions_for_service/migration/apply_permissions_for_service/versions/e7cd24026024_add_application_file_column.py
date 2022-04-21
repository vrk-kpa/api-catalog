"""Add application file column

Revision ID: e7cd24026024
Revises: 09e3ebeb1e37
Create Date: 2022-04-21 13:07:44.485191

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7cd24026024'
down_revision = '09e3ebeb1e37'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('apply_permission', sa.Column('application_filename', sa.String(255), nullable=True))



def downgrade():
    op.drop_column('apply_permission', 'application_filename')
