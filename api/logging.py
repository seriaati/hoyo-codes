from __future__ import annotations

import inspect
import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    logger.remove()
    logger.add(sys.stdout, level="INFO", backtrace=True, diagnose=False)
    logger.add(
        "logs/log_{time:YYYY-MM-DD}.log", rotation="00:00", retention="7 days", level="DEBUG"
    )

    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.DEBUG)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger_ = logging.getLogger(name)
        logger_.handlers = [InterceptHandler()]
        logger_.propagate = False
