import logging
from logging.handlers import (
    RotatingFileHandler,
)

from config import settings


class ContextFormatter(
    logging.Formatter
):
    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        fields = []

        for name in (
            "request_id",
            "http_method",
            "route",
            "status_code",
            "duration_ms",
            "client_host",
            "paper_id",
        ):
            value = getattr(
                record,
                name,
                None,
            )

            if value is not None:
                fields.append(
                    f"{name}={value}"
                )

        suffix = (
            f" | {' '.join(fields)}"
            if fields
            else ""
        )

        return (
            super().format(record)
            + suffix
        )


def setup_logging() -> None:
    logger = logging.getLogger(
        "backend"
    )

    if getattr(
        logger,
        "_research_copilot_configured",
        False,
    ):
        return

    level = getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    )

    formatter = ContextFormatter(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )

    console_handler = (
        logging.StreamHandler()
    )
    console_handler.setFormatter(
        formatter
    )

    file_handler = RotatingFileHandler(
        settings.log_dir
        / "research-copilot.log",
        maxBytes=settings.log_max_bytes,
        backupCount=(
            settings.log_backup_count
        ),
        encoding="utf-8",
    )
    file_handler.setFormatter(
        formatter
    )

    logger.setLevel(level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    setattr(
        logger,
        "_research_copilot_configured",
        True,
    )
