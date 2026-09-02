import logging
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.requests import (
    Request,
)


class RequestIdMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        request_id = (
            request.headers.get(
                "X-Request-ID"
            )
            or str(uuid4())
        )

        request.state.request_id = (
            request_id
        )

        started_at = perf_counter()
        status_code = 500

        try:
            response = await call_next(
                request
            )

            status_code = (
                response.status_code
            )

            response.headers[
                "X-Request-ID"
            ] = request_id

            return response

        finally:
            client_host = (
                request.client.host
                if request.client
                else None
            )

            logging.getLogger(
                __name__
            ).info(
                "HTTP 请求完成",
                extra={
                    "request_id":
                        request_id,
                    "http_method":
                        request.method,
                    "route":
                        request.url.path,
                    "status_code":
                        status_code,
                    "duration_ms": round(
                        (
                            perf_counter()
                            - started_at
                        )
                        * 1000,
                        2,
                    ),
                    "client_host":
                        client_host,
                },
            )
