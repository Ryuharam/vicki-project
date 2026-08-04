from sqlalchemy import BigInteger, Text, ForeignKey, LargeBinary, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Convention(Base):
    __tablename__ = "conventions"

    convention_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    repo_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("repositories.repo_id"))
    filename: Mapped[str] = mapped_column(Text)
    filecontent: Mapped[str] = mapped_column(Text)
    filehash: Mapped[bytes] = mapped_column(LargeBinary)
    uploaded_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))

    __table_args__ = (
        UniqueConstraint("repo_id", "filehash", name="unique_repo_filehash"),
    )
