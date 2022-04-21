"""Create apply permissions table

Revision ID: 09e3ebeb1e37
Revises:
Create Date: 2022-04-21 12:29:11.376163

"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.


revision = '09e3ebeb1e37'
down_revision = None
branch_labels = None
depends_on = None

def make_uuid():
    return str(uuid.uuid4())

def upgrade():
    op.create_table('apply_permission',
                    sa.Column('id', sa.types.UnicodeText, primary_key=True, default=make_uuid),
                    sa.Column('organization_id', sa.types.UnicodeText, nullable=False),
                    sa.Column('target_organization_id', sa.types.UnicodeText, nullable=False),
                    sa.Column('business_code', sa.types.UnicodeText, nullable=False),
                    sa.Column('contact_name', sa.types.UnicodeText, nullable=False),
                    sa.Column('contact_email', sa.types.UnicodeText, nullable=False),
                    sa.Column('ip_address_list', sa.types.JSON, nullable=False),
                    sa.Column('subsystem_id', sa.types.UnicodeText, nullable=False),
                    sa.Column('subsystem_code', sa.types.UnicodeText, nullable=False),
                    sa.Column('service_code_list', sa.types.JSON, nullable=False),

                    sa.Column('usage_description', sa.types.UnicodeText),
                    sa.Column('request_date', sa.types.Date),
                    )



def downgrade():
    op.drop_table('apply_permission')

