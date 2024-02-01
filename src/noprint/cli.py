"""
CLI module for NoPrint
"""
import sys
import argparse
import contextvars
from multiprocessing import cpu_count

import noprint.logger as logging

from noprint.sprint import detect_prints


log_lvl = contextvars.ContextVar("log_lvl")
error_out = contextvars.ContextVar("error_out")


def parse_args():
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
    parser.add_argument("--version", action="version", version="%(prog)s 3.1.1")
    args = parser.parse_known_intermixed_args()[0]

    err_out = args.error_out
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
    )  # cpu_count when <=0; 1 when not given; otherwise multi

    lvl = logging.ERROR if err_out else logging.WARNING

    var = contextvars.ContextVar("packages")
    var.set(packages)
    var = contextvars.ContextVar("first_only")
    var.set(first_only)
    var = contextvars.ContextVar("verbose")
    var.set(verbose)
    var = contextvars.ContextVar("very_verbose")
    var.set(very_verbose)
    var = contextvars.ContextVar("mt_threads")
    var.set(multi)

    log_lvl.set(lvl)
    error_out.set(err_out)


def cli():
    """CLI function"""
    parse_args()

    result = detect_prints()

    if result == 2:
        logging.log("Exiting with critical status", logging.CRITICAL)
    elif result == 1:
        logging.log("Print statements detected", log_lvl.get())
    else:
        logging.log("No print statements found, cheers 🍺", logging.INFO)

    if not error_out.get() and result == 1:
        result = 0
    sys.exit(result)  # 0 when success, 1 for error, 2 for critical
