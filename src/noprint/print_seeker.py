"""
Module responsible for finding print statements in python modules
"""
import os
import io
import sys
import ast
import pkgutil
import logging
from importlib.util import find_spec

import click
import chardet

logging.getLogger("chardet.universaldetector").setLevel(logging.INFO)


def _get_subpackages(package: str) -> list:
    """Grab all packages and subpackages"""
    # Patch out statements from __init__
    sys.stdout = sys.stderr = io.StringIO()
    module = find_spec(package)
    sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__

    # If module is a file or contains __init__ then yield it and set flag
    isinit = False
    if module.origin:
        isinit = str(module.origin).rsplit(sep="/", maxsplit=1)[-1] == "__init__.py"
        yield module

    # Grab submodules and all packages within the directory
    candidates = []
    sub_pkgs = []
    if not module.origin or isinit:
        pkg_path = module.submodule_search_locations
        if isinstance(pkg_path, list):
            pkg_path = pkg_path[0]
        else:  # pragma: no cover
            # Patch for _NamespacePath in Python3.7
            pkg_path = pkg_path._path[0]  # pylint: disable=protected-access

        candidates = [
            f"{module.name}.{name}"
            for name in os.listdir(pkg_path)
            if os.path.isdir(os.path.join(pkg_path, name)) and name != "__pycache__"
        ]
        sub_pkgs = [
            ".".join([package, name]) for _, name, _ in pkgutil.iter_modules([pkg_path])
        ]
    # If submodule is a directory and doesn't contain __init__ raise Warning
    candidates_missing = set(candidates) - set(sub_pkgs)
    if isinit and candidates_missing:
        for candidate in candidates_missing:
            click.secho(f"[Warning] Module {candidate} has no __init__.py", fg="yellow")
    # Patch missing submodules
    sub_pkgs = list(set(candidates) | set(sub_pkgs))

    for pkg in sub_pkgs:
        for subpkg in _get_subpackages(pkg):
            yield subpkg


def _get_prints(package: str, first_only: bool) -> list:
    """Detect print statements from packages found by _get_subpackages"""
    prints = []
    for module in _get_subpackages(package):
        file = open(module.origin, "rb")  # pylint: disable=consider-using-with
        data = file.read()
        file.close()
        encoding = chardet.detect(data)["encoding"]
        with open(module.origin, "r", encoding=encoding) as fin:
            parsed = ast.parse(fin.read())
            for node in ast.walk(parsed):
                if node.__dict__.get("id") == "print":
                    prints.append(
                        f"[{module.name}] Print at line {node.lineno} col {node.col_offset}"
                    )
                    if first_only:
                        return prints
    return prints


def detect_prints(package: str, first_only: bool = False):
    """Public wrapper for _get_prints"""
    return _get_prints(package, first_only)  # pragma: no cover
