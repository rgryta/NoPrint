"""
Logging setup for NoPrint
"""
import logging


def log(msg: str, as_error: bool):
    """Print with error or warning styling"""
    if as_error:
        logger.error(msg)
    else:
        logger.warning(msg)


logger = logging.getLogger("noprint")

formatter = logging.Formatter("%(levelname)s:%(message)s")
formatter_success = logging.Formatter("\033[1;32m%(message)s\033[1;0m")

ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(formatter)

chs = logging.StreamHandler()
chs.setLevel(logging.INFO)
chs.setFormatter(formatter_success)
chs.semit = chs.emit
chs.emit = lambda record: chs.semit(record) if record.levelno == chs.level else None

logger.addHandler(ch)
logger.addHandler(chs)
logger.setLevel(logging.INFO)

logging.addLevelName(
    logging.WARNING, f"\033[1;33m[{logging.getLevelName(logging.WARNING)}]\033[1;0m"
)
logging.addLevelName(
    logging.ERROR, f"\033[1;31m[{logging.getLevelName(logging.ERROR)}]\033[1;0m"
)
logging.addLevelName(
    logging.CRITICAL, f"\033[1;101m[{logging.getLevelName(logging.CRITICAL)}]\033[1;0m"
)
