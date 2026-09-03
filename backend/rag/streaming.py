import asyncio
import inspect
import json
import logging

from collections.abc import (
    AsyncIterator,
    Callable,
)

from backend.rag.types import (
    RagRuntimeContext,
)


logger = logging.getLogger(
    __name__
)


def sse_event(
    event: str,
    data: dict | str,
) -> bytes:
    if not isinstance(
        data,
        str,
    ):
        data = json.dumps(
            data,
            ensure_ascii=False,
        )

    payload = (
        f"event: {event}\n"
        f"data: {data}\n\n"
    )

    return payload.encode(
        "utf-8"
    )


async def stream_graph(
    *,
    graph,
    input_state,
    context: RagRuntimeContext,

    on_delta:
        Callable[
            [str],
            object,
        ]
        | None = None,

    on_done:
        Callable[
            [],
            object,
        ]
        | None = None,

) -> AsyncIterator[bytes]:
    yield sse_event(
        "meta",
        {
            "request_id":
                context.request_id,
        },
    )

    try:
        async for event in (
            graph.astream_events(
                input_state,
                context=context,
                version="v2",
            )
        ):
            event_type = event.get(
                "event"
            )

            name = event.get(
                "name"
            )

            if (
                event_type
                == "on_chat_model_start"
            ):
                yield sse_event(
                    "agent_status",
                    {
                        "status":
                            "thinking"
                    },
                )

            elif (
                event_type
                == "on_tool_start"
                and name
                == "retrieve_papers"
            ):
                yield sse_event(
                    "tool_status",
                    {
                        "tool":
                            "retrieve_papers",
                        "status":
                            "running",
                    },
                )

            elif (
                event_type
                == "on_tool_end"
                and name
                == "retrieve_papers"
            ):
                yield sse_event(
                    "tool_status",
                    {
                        "tool":
                            "retrieve_papers",
                        "status":
                            "completed",
                    },
                )

            elif (
                event_type
                == "on_chat_model_stream"
            ):
                chunk = (
                    event
                    .get(
                        "data",
                        {},
                    )
                    .get("chunk")
                )

                content = getattr(
                    chunk,
                    "content",
                    None,
                )

                if (
                    isinstance(
                        content,
                        str,
                    )
                    and content
                ):
                    await _run_hook(
                        on_delta,
                        content,
                    )

                    yield sse_event(
                        "delta",
                        {
                            "text":
                                content
                        },
                    )

        await _run_hook(
            on_done
        )

        yield sse_event(
            "done",
            {
                "status":
                    "completed"
            },
        )

    except asyncio.CancelledError:
        yield sse_event(
            "cancelled",
            {
                "status":
                    "cancelled"
            },
        )

        raise

    except Exception as exc:
        logger.exception(
            "RAG generation failed"
        )

        yield sse_event(
            "failure",
            {
                "message": (
                    "生成回答失败: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )
            },
        )


async def _run_hook(
    hook: Callable | None,
    *args,
) -> None:

    if hook is None:
        return

    result = hook(
        *args
    )

    if inspect.isawaitable(
        result
    ):
        await result