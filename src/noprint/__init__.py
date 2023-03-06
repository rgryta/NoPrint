"""
Initial module for NoPrint containing constants, statics, and logger setup
"""
import logging


class ImportException(Exception):
    "Raised when there was import exception in print_seeker"


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
