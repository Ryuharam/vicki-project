from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    login: Mapped[str] = mapped_column(Text, comment="Github user login name")
    avatar_url: Mapped[str] = mapped_column(Text, comment="Github user profile url")
