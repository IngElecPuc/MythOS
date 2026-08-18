import logging
import sys

from src.config.config import get_settings


class LoggingConfigurator:
    @staticmethod
    def configure() -> None:
        level = get_settings().log_level
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
            force=True,
        )

        for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            logging.getLogger(logger_name).setLevel(level)


def configure_logging() -> None:
    LoggingConfigurator.configure()