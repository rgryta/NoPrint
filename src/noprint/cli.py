"""
CLI module for NoPrint
"""
import os
import sys
import logging
import argparse

from noprint.logger import log
from noprint.sprint import detect_prints
from noprint.exceptions import ImportException


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
            log(exc, logging.CRITICAL)

    if exceptions:
        sys.exit(2)

    if prints:
        log("Print statements detected", logging)
        for prt in prints:
            log(prt, logging.ERROR if as_error else logging.WARNING)
        if as_error:
            sys.exit(1)
        sys.exit(0)
    log("No print statements found, cheers 🍺", logging.INFO)
    sys.exit(0)
