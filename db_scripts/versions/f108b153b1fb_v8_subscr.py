"""V8_subscr

Revision ID: f108b153b1fb
Revises: 6ab9a02394bd
Create Date: 2017-07-24 17:43:43.416338

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f108b153b1fb'
down_revision = '6ab9a02394bd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('subscriptions', sa.Column('end', sa.DateTime(), nullable=True))
    op.add_column('subscriptions', sa.Column('start', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('subscriptions', 'start')
    op.drop_column('subscriptions', 'end')
    # ### end Alembic commands ###
