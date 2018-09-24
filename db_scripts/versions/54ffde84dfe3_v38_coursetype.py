"""V38_coursetype

Revision ID: 54ffde84dfe3
Revises: 85825d39c889
Create Date: 2017-09-01 16:02:18.740791

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54ffde84dfe3'
down_revision = '85825d39c889'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('elements', sa.Column('coursetype', sa.Enum('short', 'long'), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('elements', 'coursetype')
    # ### end Alembic commands ###
