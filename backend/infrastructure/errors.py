import logging

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.responses import (
    JSONResponse,
)


logger = logging.getLogger(__name__)


def request_id_from(
    request: Request,
) -> str:
    return getattr(
        request.state,
        "request_id",
        "unknown",
    )


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    details=None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "request_id": request_id,
            "details": details,
        },
        headers={
            "X-Request-ID": request_id,
        },
    )


def register_exception_handlers(
    app: FastAPI,
) -> None:
    @app.exception_handler(
        HTTPException
    )
    async def handle_http_error(
        request: Request,
        exc: HTTPException,
    ):
        request_id = request_id_from(
            request
        )

        return error_response(
            status_code=exc.status_code,
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            request_id=request_id,
        )

    @app.exception_handler(
        RequestValidationError
    )
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ):
        request_id = request_id_from(
            request
        )

        details = [
            {
                "location": ".".join(
                    str(part)
                    for part in error["loc"]
                ),
                "type": error["type"],
            }
            for error in exc.errors()
        ]

        return error_response(
            status_code=422,
            code="INVALID_REQUEST",
            message="请求参数不正确",
            request_id=request_id,
            details=details,
        )

    @app.exception_handler(
        Exception
    )
    async def handle_unexpected_error(
        request: Request,
        exc: Exception,
    ):
        request_id = request_id_from(
            request
        )

        logger.exception(
            "未处理的接口异常",
            exc_info=exc,
            extra={
                "request_id": request_id,
                "http_method":
                    request.method,
                "route":
                    request.url.path,
            },
        )

        return error_response(
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="服务内部发生错误",
            request_id=request_id,
        )
