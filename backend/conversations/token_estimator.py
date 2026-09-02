import math


MESSAGE_OVERHEAD = 8
SAFETY_MARGIN = 1.10


def estimate_text_tokens(
    text: str,
) -> int:
    byte_count = len(
        text.encode(
            "utf-8"
        )
    )

    estimate = (
        math.ceil(
            byte_count / 3
        )
        + MESSAGE_OVERHEAD
    )

    return math.ceil(
        estimate
        * SAFETY_MARGIN
    )


def estimate_messages_tokens(
    messages,
) -> int:
    return sum(
        estimate_text_tokens(
            message.content
        )
        for message in messages
    )