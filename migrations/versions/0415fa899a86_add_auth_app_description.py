"""Add auth app description

Revision ID: 0415fa899a86
Revises: a1135db7a8e7
Create Date: 2015-12-30 19:26:56.603918

"""

# revision identifiers, used by Alembic.
revision = '0415fa899a86'
down_revision = 'a1135db7a8e7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('wr_auth_apps', sa.Column('app_description', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('wr_auth_apps', 'app_description')
    ### end Alembic commands ###
