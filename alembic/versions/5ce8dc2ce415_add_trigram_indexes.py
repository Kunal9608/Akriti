"""add_trigram_indexes

Revision ID: 5ce8dc2ce415
Revises: 6742aa9f0232
Create Date: 2026-07-20 10:45:05.677781

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ce8dc2ce415'
down_revision: Union[str, Sequence[str], None] = '6742aa9f0232'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        op.execute("CREATE INDEX IF NOT EXISTS idx_patient_name_trgm ON patients USING gin (name gin_trgm_ops);")
        op.execute("CREATE INDEX IF NOT EXISTS idx_patient_mobile_trgm ON patients USING gin (mobile gin_trgm_ops);")
        op.execute("CREATE INDEX IF NOT EXISTS idx_patient_code_trgm ON patients USING gin (patient_code gin_trgm_ops);")


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_patient_code_trgm;")
        op.execute("DROP INDEX IF EXISTS idx_patient_mobile_trgm;")
        op.execute("DROP INDEX IF EXISTS idx_patient_name_trgm;")
