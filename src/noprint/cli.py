"""
Main CLI module for NoPrint
"""
import os
import sys
import logging
import argparse

from . import ImportException
from .print_seeker import detect_prints

logger = logging.getLogger("noprint")


def _log(msg: str, as_error: bool):
    """Print with error or warning styling"""
    if as_error:
        logger.error(msg)
    else:
        logger.warning(msg)


def cli():
    """No prints are allowed!"""
    parser = argparse.ArgumentParser(prog="NoPrint", allow_abbrev=False)
    parser.add_argument("-e", "--as-error", action="store_true")
    parser.add_argument("-f", "--first-only", action="store_true")
    parser.add_argument("packages", nargs="*", type=str)
    args = parser.parse_known_intermixed_args()[0]

    as_error = args.as_error
    first_only = args.first_only
    packages = args.packages

    # Allow to search for packges in current directory (mainly for tests directories - not available in sys.modules)
    sys.path.append(os.getcwd())

    prints = []
    exceptions = False
    for package in packages:
        try:
            detected = detect_prints(package, first_only)
            prints = prints + detected
        except ImportException as exc:
            exceptions = True
            logger.critical(exc)

    if exceptions:
        sys.exit(2)

    if prints:
        _log("Print statements detected", as_error)
        for prt in prints:
            _log(prt, as_error)
        if as_error:
            sys.exit(1)
        sys.exit(0)
    logger.info("No print statements found, cheers 🍺")
    sys.exit(0)
