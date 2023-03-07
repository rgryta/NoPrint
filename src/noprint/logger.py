"""
Logging setup for NoPrint
"""
import logging

from logging import INFO, WARNING, ERROR, CRITICAL


def log(msg: str, level: int):
    """Print with error or warning styling"""
    if level == INFO:
        logger.info(msg)
    elif level == WARNING:
        logger.warning(msg)
    elif level == ERROR:
        logger.error(msg)
    elif level == CRITICAL:
        logger.critical(msg)


logger = logging.getLogger("noprint")

formatter = logging.Formatter("%(levelname)s:%(message)s")
formatter_success = logging.Formatter("\033[1;32m%(message)s\033[1;0m")

ch = logging.StreamHandler()
ch.setLevel(WARNING)
ch.setFormatter(formatter)

chs = logging.StreamHandler()
chs.setLevel(INFO)
chs.setFormatter(formatter_success)
chs.semit = chs.emit
chs.emit = lambda record: chs.semit(record) if record.levelno == chs.level else None

logger.addHandler(ch)
logger.addHandler(chs)
logger.setLevel(logging.INFO)

logging.addLevelName(WARNING, f"\033[1;33m[{logging.getLevelName(WARNING)}]\033[1;0m")
logging.addLevelName(ERROR, f"\033[1;31m[{logging.getLevelName(ERROR)}]\033[1;0m")
logging.addLevelName(
    CRITICAL, f"\033[1;101m[{logging.getLevelName(CRITICAL)}]\033[1;0m"
)
# LogLevel.INFO doesn't display levelname, so not needed
