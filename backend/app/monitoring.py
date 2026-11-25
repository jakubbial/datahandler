import logging
import os
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("datahandler.bdl")

MONITORING_ENV_VAR = "BDL_MONITORING"
LOG_FILE_ENV_VAR = "BDL_MONITORING_LOG_FILE"
DEFAULT_LOG_FILE = "logs/bdl-monitoring.log"
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3


def configure_monitoring() -> None:
    """Log BDL requests and cache lookups to stderr and a file.

    Enabled by default; set BDL_MONITORING to 0, false, no or off to disable.
    """
    if os.environ.get(MONITORING_ENV_VAR, "").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s %(name)s %(message)s")
        handlers: list[logging.Handler] = [logging.StreamHandler()]
        log_file = os.environ.get(LOG_FILE_ENV_VAR, DEFAULT_LOG_FILE).strip()
        if log_file:
            try:
                os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
                handlers.append(
                    RotatingFileHandler(
                        log_file,
                        maxBytes=LOG_MAX_BYTES,
                        backupCount=LOG_BACKUP_COUNT,
                        encoding="utf-8",
                    )
                )
            except OSError:
                pass  # Fall back to stderr only.
        for handler in handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def log_cache(cache: str, outcome: str, key: object) -> None:
    logger.info("cache=%s outcome=%s key=%s", cache, outcome, key)
