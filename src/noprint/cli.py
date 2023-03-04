"""
Main CLI module for NoPrint
"""
import os
import sys
import logging

import click

from .print_seeker import detect_prints

logging.basicConfig(level=logging.NOTSET)


@click.pass_context
def _log(ctx, msg: str):
    """Print with error or warning styling"""
    if ctx.params["as_error"]:
        click.secho(msg, fg="red")
    else:
        click.secho(msg, fg="yellow")


@click.command()
@click.option(
    "-f",
    "--first-only",
    is_flag=True,
    show_default=True,
    default=False,
    help="Exit on first print found.",
)
@click.option(
    "-e",
    "--as-error",
    is_flag=True,
    show_default=True,
    default=False,
    help="Exit with error when print is found (default is Warning).",
)
@click.argument("packages", nargs=-1)
def cli(first_only, as_error, packages):
    """No prints are allowed!"""
    # Allow to search for packges in current directory (mainly for tests directories - not available in sys.modules)
    sys.path.append(os.getcwd())
    prints = []
    for package in packages:
        prints = prints + detect_prints(package, first_only)

    if prints:
        _log("Print statements detected at:")
        for prt in prints:
            _log(prt)
        if as_error:
            sys.exit(1)
        sys.exit(0)
    click.secho("Success! No prints detected.", fg="green")
    sys.exit(0)
