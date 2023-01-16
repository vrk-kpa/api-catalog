"""add created timestamp column

Revision ID: 244dd92f445e
Revises: d7db14126049
Create Date: 2023-01-14 20:13:43.577678

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '244dd92f445e'
down_revision = 'd7db14126049'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('apply_permission', sa.Column('created', sa.DateTime, nullable=False, server_default=sa.func.now()))


def downgrade():
    op.drop_column('apply_permission', 'created')
