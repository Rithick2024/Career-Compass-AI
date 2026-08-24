"""
Application-wide logging configuration.

Called once at startup from `app.main`. Uses the stdlib `logging`
module with `dictConfig` so behavior is explicit and easy to extend
(e.g. adding a JSON formatter or a file/rotating handler later)
without touching call sites elsewhere in the app.
"""

import logging
import logging.config

from app.core.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    log_level = settings.LOG_LEVEL.upper()

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": LOG_FORMAT,
                "datefmt": DATE_FORMAT,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            # SQLAlchemy's own loggers — keep quiet unless DEBUG/DB_ECHO
            "sqlalchemy.engine": {
                "level": "INFO" if settings.DB_ECHO else "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Convenience accessor: `logger = get_logger(__name__)`."""
    return logging.getLogger(name)
