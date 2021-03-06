"""Reinit

Revision ID: 2ae8c888bb30
Revises: None
Create Date: 2016-01-10 15:52:38.898718

"""

# revision identifiers, used by Alembic.
revision = '2ae8c888bb30'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('wr_options',
    sa.Column('option_ID', sa.Integer(), nullable=False),
    sa.Column('option_name', sa.Text(), nullable=True),
    sa.Column('option_value', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('option_ID')
    )
    op.create_table('wr_roles',
    sa.Column('role_ID', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('counts', sa.Integer(), nullable=False),
    sa.Column('permissions', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('role_ID'),
    sa.UniqueConstraint('name')
    )
    op.create_table('wr_taxonomy',
    sa.Column('taxonomy_ID', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('parent', sa.Integer(), nullable=False),
    sa.Column('counts', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=64), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('thumb', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('taxonomy_ID')
    )
    op.create_table('wr_users',
    sa.Column('user_ID', sa.Integer(), nullable=False),
    sa.Column('user_login', sa.Text(), nullable=False),
    sa.Column('user_pass', sa.Text(), nullable=False),
    sa.Column('user_displayname', sa.Text(), nullable=True),
    sa.Column('user_email', sa.Text(), nullable=True),
    sa.Column('avatar_hash', sa.Text(), nullable=True),
    sa.Column('user_url', sa.Text(), nullable=True),
    sa.Column('user_registered', sa.DateTime(), nullable=False),
    sa.Column('user_lastseen', sa.DateTime(), nullable=False),
    sa.Column('user_activation_key', sa.Text(), nullable=True),
    sa.Column('user_confirmed', sa.Boolean(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['wr_roles.role_ID'], ),
    sa.PrimaryKeyConstraint('user_ID'),
    sa.UniqueConstraint('user_email'),
    sa.UniqueConstraint('user_login')
    )
    op.create_table('wr_auth_apps',
    sa.Column('app_ID', sa.Integer(), nullable=False),
    sa.Column('user_ID', sa.Integer(), nullable=True),
    sa.Column('app_key', sa.String(length=32), nullable=False),
    sa.Column('app_secret', sa.String(length=32), nullable=False),
    sa.Column('app_url', sa.Text(), nullable=False),
    sa.Column('app_name', sa.String(length=32), nullable=False),
    sa.Column('app_created', sa.DateTime(), nullable=False),
    sa.Column('app_request_count', sa.Integer(), nullable=False),
    sa.Column('app_level', sa.Integer(), nullable=False),
    sa.Column('app_description', sa.Text(), nullable=True),
    sa.Column('app_status', sa.Integer(), nullable=True),
    sa.Column('app_icon', sa.Text(), nullable=True),
    sa.Column('access_token', sa.Text(), nullable=True),
    sa.Column('token_expire', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_ID'], ['wr_users.user_ID'], ),
    sa.PrimaryKeyConstraint('app_ID'),
    sa.UniqueConstraint('app_key'),
    sa.UniqueConstraint('app_name')
    )
    op.create_table('wr_usermeta',
    sa.Column('meta_ID', sa.Integer(), nullable=False),
    sa.Column('user_ID', sa.Integer(), nullable=True),
    sa.Column('meta_key', sa.Text(), nullable=True),
    sa.Column('meta_value', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_ID'], ['wr_users.user_ID'], ),
    sa.PrimaryKeyConstraint('meta_ID')
    )
    op.create_table('wr_videos',
    sa.Column('video_ID', sa.Integer(), nullable=False),
    sa.Column('video_author', sa.Integer(), nullable=True),
    sa.Column('video_date', sa.DateTime(), nullable=False),
    sa.Column('video_title', sa.Text(), nullable=True),
    sa.Column('video_description', sa.Text(), nullable=True),
    sa.Column('video_link', sa.Text(), nullable=True),
    sa.Column('video_vid', sa.Text(), nullable=True),
    sa.Column('video_cover', sa.Text(), nullable=True),
    sa.Column('video_duration', sa.Float(), nullable=False),
    sa.Column('video_sd_urls', sa.Text(), nullable=True),
    sa.Column('video_hd_urls', sa.Text(), nullable=True),
    sa.Column('video_uhd_urls', sa.Text(), nullable=True),
    sa.Column('video_status', sa.Text(), nullable=False),
    sa.Column('video_from', sa.Text(), nullable=False),
    sa.Column('video_score', sa.Float(), nullable=False),
    sa.Column('video_play_count', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['video_author'], ['wr_users.user_ID'], ),
    sa.PrimaryKeyConstraint('video_ID')
    )
    op.create_index(op.f('ix_wr_videos_video_play_count'), 'wr_videos', ['video_play_count'], unique=False)
    op.create_table('wr_terms',
    sa.Column('term_ID', sa.Integer(), nullable=False),
    sa.Column('video_ID', sa.Integer(), nullable=True),
    sa.Column('taxonomy_ID', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['taxonomy_ID'], ['wr_taxonomy.taxonomy_ID'], ),
    sa.ForeignKeyConstraint(['video_ID'], ['wr_videos.video_ID'], ),
    sa.PrimaryKeyConstraint('term_ID')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('wr_terms')
    op.drop_index(op.f('ix_wr_videos_video_play_count'), table_name='wr_videos')
    op.drop_table('wr_videos')
    op.drop_table('wr_usermeta')
    op.drop_table('wr_auth_apps')
    op.drop_table('wr_users')
    op.drop_table('wr_taxonomy')
    op.drop_table('wr_roles')
    op.drop_table('wr_options')
    ### end Alembic commands ###
