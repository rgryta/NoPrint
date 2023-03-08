"""
Module responsible for finding print statements in python modules
"""
import os
import io
import re
import sys
import ast
import pkgutil
import functools
from typing import Optional, Union, Tuple
from importlib.util import find_spec
from importlib.machinery import ModuleSpec
from multiprocessing.pool import Pool

import noprint.logger as logging

from noprint import ENCODING_CAPTURE
from noprint.exceptions import ImportException


def _get_spec(package, in_cwd: bool = True) -> Optional[ModuleSpec]:
    sys.stdout = sys.stderr = io.StringIO()
    try:
        # Allow to search for packges in current directory (mainly for tests directories - not available in sys.modules)
        if in_cwd:
            sys.path.insert(0, os.getcwd())
        module = find_spec(package)
    except Exception as exc:
        raise ImportException(
            f"Module [{package}] raised {type(exc).__name__} on import"
        ) from exc
    finally:
        if in_cwd:
            sys.path.remove(os.getcwd())
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__

    return module


def _get_module_path(module: ModuleSpec):
    pkg_path = module.submodule_search_locations
    if isinstance(pkg_path, list):
        pkg_path = pkg_path[0]
    else:  # pragma: no cover
        # Patch for _NamespacePath in Python3.7
        pkg_path = pkg_path._path[0]  # pylint: disable=protected-access
    return pkg_path


def _get_subpackages(
    package: str, verbose: bool = False
) -> Union[ModuleSpec, ImportException]:
    """Grab all packages and subpackages"""
    # Patch out statements from __init__
    try:
        module = _get_spec(package)
    except ImportException as exc:
        yield exc
        return  # pragma: no cover
    try:
        system_module = _get_spec(package, in_cwd=False)
    except ImportException:  # pragma: no cover
        pass

    if not module:
        yield ImportException(
            f"Module [{package}] is not present in current environment, directory or PYTHONPATH"
        )
        return

    if module and not system_module and verbose:
        logging.log(f"Module [{package}] is not installed", logging.WARNING)
    elif module != system_module and verbose:
        logging.log(
            f"Module [{package}] is overshadowing installed module", logging.WARNING
        )

    # If module is a file or contains __init__ then yield it and set flag
    isinit = False
    if module.origin:
        isinit = str(module.origin).rsplit(sep="/", maxsplit=1)[-1] == "__init__.py"
        yield module

    # Grab submodules and all packages within the directory
    candidates = []
    sub_pkgs = []
    if not module.origin or isinit:
        pkg_path = _get_module_path(module)
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
    if isinit and candidates_missing and verbose:
        for candidate in candidates_missing:
            logging.log(f"Module [{candidate}] has no __init__.py", logging.WARNING)
    # Patch missing submodules
    sub_pkgs = list(set(candidates) | set(sub_pkgs))

    for pkg in sub_pkgs:
        for subpkg in _get_subpackages(pkg):
            yield subpkg


def _packages_iter(packages: tuple, verbose: bool = False):
    """Iterate over all provided subpackages"""
    for package in packages:  # pragma: no cover
        for subpackage in _get_subpackages(package, verbose):
            yield subpackage


def _parse_pyfile(module, first_only):
    """Method for parsing python source code files to look for prints"""
    if isinstance(module, ImportException):
        return ([], module)

    prints = []
    encoding = "utf-8"
    # First two lines of Python source code have to be ASCII compatible
    # PEP-8, PEP-263, PEP-3120
    with open(module.origin, "r", encoding="utf-8") as file:
        for _ in range(2):  # Check 1st two lines
            found = re.search(ENCODING_CAPTURE, file.readline())
            if found:
                encoding = found.group(1)
                break

    with open(module.origin, "r", encoding=encoding) as file:
        parsed = ast.parse(file.read())
        clear = True
        for node in ast.walk(parsed):
            if node.__dict__.get("id") == "print":
                clear = False
                prints.append(
                    (
                        f"[{module.name}] Line: {node.lineno}",
                        True,
                    )
                )
                if first_only:
                    return (prints, None)
        if clear:
            prints.append(
                (
                    f"[CLEAR]:[{module.name}]",
                    False,
                )
            )
    return (prints, None)


def _get_prints(
    packages: tuple,
    first_only: bool = False,
    verbose: bool = False,
    pool_threads: int = 1,
) -> Tuple[list, list]:
    """Detect print statements from packages found by _get_subpackages"""
    prints = []
    exceptions = []

    func = functools.partial(_parse_pyfile, first_only=first_only)
    with Pool(pool_threads) as pool:
        for found, exception in pool.imap(func, _packages_iter(packages, verbose)):
            if found:
                prints = prints + found
            elif exception:
                exceptions.append(exception)
            if any(printed for _, printed in found) and first_only:
                break
    return (
        prints,
        exceptions,
    )


def detect_prints(
    packages: tuple,
    first_only: bool = False,
    verbose: bool = False,
    pool_threads: int = 1,
) -> Tuple[list, list]:
    """Public wrapper for _get_prints"""
    return _get_prints(packages, first_only, verbose, pool_threads)  # pragma: no cover
