"""
CLI module for NoPrint
"""
import sys
import argparse
from multiprocessing import cpu_count

import noprint.logger as logging

from noprint.sprint import detect_prints


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
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="provide more analysis information (use multiple v's to increase logging level)",
    )
    parser.add_argument(
        "packages",
        help="which packages/modules to check, syntax: <package>[.<module> ...], e.g. noprint or noprint.cli",
        nargs="+",
        type=str,
    )
    parser.add_argument(
        "-m",
        "--multi",
        nargs="?",
        const=1,
        type=int,
        help="set how many threads to use",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")
    args = parser.parse_known_intermixed_args()[0]

    error_out = args.error_out
    first_only = args.first_only
    verbose = bool(args.verbose)
    very_verbose = args.verbose >= 2
    packages = args.packages
    multi = (
        cpu_count()
        if args.multi is not None and args.multi <= 0
        else args.multi
        if args.multi
        else 1
    )

    lvl = logging.ERROR if error_out else logging.WARNING

    prints, exceptions = detect_prints(packages, first_only, verbose, multi)

    exitcode = 0
    detected = any(is_print for _, is_print in prints)

    if error_out and detected:
        exitcode = 1

    if exceptions:
        for exc in exceptions:
            logging.log(exc.args[0], logging.CRITICAL)
        exitcode = 2

    if verbose:
        for prt in prints:
            if prt[1]:
                logging.log(prt[0], lvl)
            elif very_verbose:
                logging.log(prt[0], logging.INFO)

    if exceptions:
        logging.log("Exiting with critical status", logging.CRITICAL)
    elif detected:
        logging.log("Print statements detected", lvl)
    else:
        logging.log("No print statements found, cheers 🍺", logging.INFO)
    sys.exit(exitcode)  # 0 when success, 1 for error, 2 for critical
