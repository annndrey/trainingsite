"""V15_emailconfirmedflag

Revision ID: 16f5b7e2f58f
Revises: a9abe302ac42
Create Date: 2017-07-26 13:34:02.503462

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16f5b7e2f58f'
down_revision = 'a9abe302ac42'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_confirmed', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'is_confirmed')
    # ### end Alembic commands ###