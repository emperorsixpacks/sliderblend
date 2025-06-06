"""added telegram user id

Revision ID: c2175c5a1973
Revises: ea79aa59b531
Create Date: 2025-04-10 17:41:41.604320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import pgvector


# revision identifiers, used by Alembic.
revision: str = 'c2175c5a1973'
down_revision: Union[str, None] = 'ea79aa59b531'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('telegram_user_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.drop_column('users', 'command_count')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('command_count', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_column('users', 'telegram_user_id')
    # ### end Alembic commands ###
