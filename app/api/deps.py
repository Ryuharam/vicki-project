from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.container import Container


def get_container(request: Request) -> Container:
    """lifespan에서 조립해둔 container를 꺼냅니다."""
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


async def get_db(container: ContainerDep):
    """요청 단위 DB 세션을 열고, 응답 후 닫습니다."""
    async with container.rdb.session_maker() as session:
        yield session


DbDep = Annotated[AsyncSession, Depends(get_db)]
