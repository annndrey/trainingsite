"""V13_publishedflag

Revision ID: 53c33b570c6c
Revises: 389bac99f4db
Create Date: 2017-07-26 13:27:36.949112

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53c33b570c6c'
down_revision = '389bac99f4db'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('courses', sa.Column('is_published', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('courses', 'is_published')
    # ### end Alembic commands ###