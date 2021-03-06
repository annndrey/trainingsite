"""V17_articles

Revision ID: a9341c0bdffe
Revises: a5d0e6a5c1a0
Create Date: 2017-08-01 13:47:23.204368

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9341c0bdffe'
down_revision = 'a5d0e6a5c1a0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('articles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('header', sa.Text(), nullable=True),
    sa.Column('body', sa.Text(), nullable=True),
    sa.Column('is_published', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=op.f('fk_articles_author_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_articles'))
    )
    op.add_column(u'media', sa.Column('comments', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'media', 'comments')
    op.drop_table('articles')
    # ### end Alembic commands ###
