"""add distance_bin column

Revision ID: c137e7385dd7
Revises: 245d4da5b9e4
Create Date: 2020-03-20 13:59:19.374167

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c137e7385dd7'
down_revision = '245d4da5b9e4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('race', sa.Column('distance_bin', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('race', 'distance_bin')
    # ### end Alembic commands ###
