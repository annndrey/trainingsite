"""V25_coursepreview

Revision ID: b7f414e13677
Revises: 535c0940ce17
Create Date: 2017-08-09 12:01:30.201274

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7f414e13677'
down_revision = '535c0940ce17'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('courses', sa.Column('preview', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('courses', 'preview')
    # ### end Alembic commands ###
