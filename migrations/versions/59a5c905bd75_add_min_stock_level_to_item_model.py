"""Add min_stock_level to Item model

Revision ID: 59a5c905bd75
Revises: 530acaf7ceae
Create Date: 2024-03-03 18:51:23.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59a5c905bd75'
down_revision = '530acaf7ceae'
branch_labels = None
depends_on = None


def upgrade():
    # First add the column as nullable
    with op.batch_alter_table('item') as batch_op:
        batch_op.add_column(sa.Column('min_stock_level', sa.Integer(), nullable=True))
    
    # Update existing rows with default value
    op.execute("UPDATE item SET min_stock_level = 0 WHERE min_stock_level IS NULL")
    
    # Now make the column NOT NULL
    with op.batch_alter_table('item') as batch_op:
        batch_op.alter_column('min_stock_level',
                            existing_type=sa.Integer(),
                            nullable=False)


def downgrade():
    with op.batch_alter_table('item') as batch_op:
        batch_op.drop_column('min_stock_level')
