from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Repository(Base):
    __tablename__ = "repositories"

    repo_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    installation_id: Mapped[int] = mapped_column(BigInteger)
    full_name: Mapped[str] = mapped_column(Text)
