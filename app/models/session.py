import uuid
from datetime import datetime

from sqlalchemy import Text, BigInteger, Uuid, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
