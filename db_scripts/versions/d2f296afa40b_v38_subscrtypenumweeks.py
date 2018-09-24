"""V38_subscrtypenumweeks

Revision ID: d2f296afa40b
Revises: 2c91fab23c54
Create Date: 2017-09-01 18:49:15.945284

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2f296afa40b'
down_revision = '2c91fab23c54'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('subscriptiontypes', sa.Column('numweeks', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('subscriptiontypes', 'numweeks')
    # ### end Alembic commands ###