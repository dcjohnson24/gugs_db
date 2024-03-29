"""Drop the Runner table

Revision ID: 3806c09754dc
Revises: 2524785502b4
Create Date: 2020-04-14 19:19:16.321657

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3806c09754dc'
down_revision = '2524785502b4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('runner_contact', 'runner_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('runner_contact', sa.Column('runner_id', sa.BIGINT(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
