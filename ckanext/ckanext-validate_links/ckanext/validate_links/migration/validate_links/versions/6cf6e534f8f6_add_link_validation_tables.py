"""add link validation tables

Revision ID: 6cf6e534f8f6
Revises:
Create Date: 2025-02-04 11:10:50.240282

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '6cf6e534f8f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'link_validation_result' not in tables:
        op.create_table('link_validation_result',
                        sa.Column('id', sa.UnicodeText, primary_key=True),
                        sa.Column('type', sa.UnicodeText),
                        sa.Column('timestamp', sa.DateTime),
                        sa.Column('url', sa.UnicodeText, nullable=False),
                        sa.Column('reason', sa.UnicodeText, nullable=False),
                        )

    if 'link_validation_referrer' not in tables:
        op.create_table('link_validation_referrer',
                        sa.Column('id', sa.UnicodeText, primary_key=True),
                        sa.Column('result_id', sa.UnicodeText, sa.ForeignKey('link_validation_result.id')),
                        sa.Column('url', sa.UnicodeText, nullable=False),
                        sa.Column('organization', sa.UnicodeText, nullable=True),
                        )


def downgrade():
    op.drop_table('link_validation_result')
    op.drop_table('link_validation_referrer')
