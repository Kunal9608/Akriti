"""FaceEmbedding model — pgvector VECTOR(128) column for face recognition."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, SmallInteger, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.db import Base

try:
    import os
    if os.getenv("DISABLE_PGVECTOR", "false").lower() == "true":
        raise ImportError("Manually disabled")
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    from sqlalchemy import Text
    VECTOR_AVAILABLE = False


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # 128-dim vector — pgvector if available, else stored as JSON text
    embedding = Column(Vector(128) if VECTOR_AVAILABLE else Text, nullable=False)
    sample_index = Column(SmallInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="face_embeddings")
