from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.exceptions.custom_exception import BaseAPIException


async def global_exception_handler(request: Request, exc: BaseAPIException):
    return JSONResponse(
        status_code=exc.status_code, content={"success": False, "message": exc.detail}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = []

    for error in exc.errors():
        location = ", ".join(str(loc) for loc in error["loc"])

        raw_msg = error["msg"]

        input_value = error.get("input", "값 없음")

        error_details.append(
            {"field": location, "reason": raw_msg, "input_given": input_value}
        )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "데이터 유효성 검사에 실패했습니다.",
            "errors": error_details,
        },
    )
