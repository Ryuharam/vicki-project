from typing import Annotated

from fastapi import Depends, Request

from app.core.container import Container


def get_container(request: Request) -> Container:
    """lifespan에서 조립해둔 container를 꺼냅니다."""
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]
