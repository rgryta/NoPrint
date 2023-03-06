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
    parser = argparse.ArgumentParser(
        prog="NoPrint",
        description="Do not allow prints in your code.",
        epilog="Thank you for using NoPrint",
        allow_abbrev=False,
    )
    parser.add_argument(
        "-e",
        "--error-out",
        action="store_true",
        help="exit with error when print is found (by default only warnings are shown)",
    )
    parser.add_argument(
        "-f", "--first-only", action="store_true", help="finish on first print found"
    )
    parser.add_argument(
        "packages",
        help="which packages/modules to check, syntax: <package>[.<module> ...], e.g. noprint or noprint.cli",
        nargs="*",
        type=str,
    )
    args = parser.parse_known_intermixed_args()[0]

    error_out = args.error_out
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
        lvl = logging.ERROR if error_out else logging.WARNING
        log("Print statements detected", lvl)
        for prt in prints:
            log(prt, lvl)
        if error_out:
            sys.exit(1)
        sys.exit(0)
    log("No print statements found, cheers 🍺", logging.INFO)
    sys.exit(0)
