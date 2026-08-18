import logging
import re
import sys

from src.config.config import Settings
from src.core.context import request_id_context


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        return True


class SensitiveDataFilter(logging.Filter):
    _patterns = (
        re.compile(r"(?i)(authorization|cookie|set-cookie)=[^|\s]+"),
        re.compile(
            r"(?i)(password|access_token|refresh_token|api_key|client_secret)"
            r"([=:]\s*)[^,|\s]+"
        ),
    )

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in self._patterns:
            message = pattern.sub(lambda match: f"{match.group(1)}=[REDACTED]", message)
        record.msg = message
        record.args = ()
        return True


class LoggingConfigurator:
    @staticmethod
    def configure(settings: Settings) -> None:
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(RequestContextFilter())
        handler.addFilter(SensitiveDataFilter())
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | "
                "request_id=%(request_id)s | %(message)s"
            )
        )

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(settings.log_level)

        for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            logging.getLogger(logger_name).setLevel(settings.log_level)


def configure_logging(settings: Settings) -> None:
    LoggingConfigurator.configure(settings)
