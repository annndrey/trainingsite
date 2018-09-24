"""V10_passwordreset

Revision ID: 72dddaa36bcc
Revises: c600913fa8af
Create Date: 2017-07-25 14:44:27.714916

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72dddaa36bcc'
down_revision = 'c600913fa8af'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('lastchanged', sa.DateTime(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'lastchanged')
    # ### end Alembic commands ###