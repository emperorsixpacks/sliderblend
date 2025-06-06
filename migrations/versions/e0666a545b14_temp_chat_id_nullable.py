"""temp: chat id nullable

Revision ID: e0666a545b14
Revises: 13c4a547820c
Create Date: 2025-04-11 14:45:52.237701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import pgvector


# revision identifiers, used by Alembic.
revision: str = 'e0666a545b14'
down_revision: Union[str, None] = '13c4a547820c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'telegram_username',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('users', 'telegram_user_id',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('users', 'chat_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'chat_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('users', 'telegram_user_id',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('users', 'telegram_username',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###
