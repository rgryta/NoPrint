"""
Module responsible for finding print statements in python modules
"""
import os
import re
import ast
import pkgutil
import functools
from typing import Tuple
from pathlib import Path
from multiprocessing.pool import Pool

import noprint.logger as logging

from noprint import ENCODING_CAPTURE
from noprint.module import Module
from noprint.exceptions import ImportException, ParentModuleNotFoundException


def _get_module(package, verbose):
    """Get Module of the package"""
    try:
        module = Module(package)
    except ParentModuleNotFoundException as exc:
        raise ImportException(exc) from exc
    if not module:
        raise ImportException(
            f"Module [{package}] is not present in current environment, directory or PYTHONPATH"
        )

    system_module = None
    try:
        system_module = Module(package, in_cwd=False)
    except ParentModuleNotFoundException:  # pragma: no cover
        pass

    if not system_module and verbose:
        logging.log(f"Module [{package}] is not installed", logging.WARNING)
    elif (
        module != system_module
        and system_module
        and len(system_module.origin) > 0
        and verbose
    ):
        logging.log(
            f"Module [{package}] is overshadowing installed module", logging.WARNING
        )

    return module


def _get_subpackages(package, verbose, module):
    """Get all candidates for submodules"""
    # If module is a file or contains __init__ then yield it and set flag
    isinit = False
    if module.origin:
        candidates = [Path(orig).name for orig in module.origin]
        isinit = "__init__.py" in candidates

    # Grab submodules and all packages within the directory
    candidates = []
    sub_pkgs = []
    if not module.origin or isinit:
        pkg_path = module.search_path
        if pkg_path:  # Found non-.py file as submodule
            candidates = [
                f"{module.name}.{name}"
                for name in os.listdir(pkg_path)
                if os.path.isdir(os.path.join(pkg_path, name)) and name != "__pycache__"
            ]
            sub_pkgs = [
                ".".join([package, name])
                for _, name, _ in pkgutil.iter_modules([pkg_path])
            ]
    # If submodule is a directory and doesn't contain __init__ raise Warning
    candidates_missing = set(candidates) - set(sub_pkgs)
    if isinit and candidates_missing and verbose:
        for candidate in candidates_missing:
            logging.log(f"Module [{candidate}] has no __init__.py", logging.WARNING)
    # Patch missing submodules
    return list(set(candidates) | set(sub_pkgs))


def _parse_module(package: str, verbose: bool = False):
    """Grab all packages and subpackages"""
    module = _get_module(package, verbose)

    sub_pkgs = _get_subpackages(package, verbose, module)

    funcs = []
    for pkg in sub_pkgs:
        funcs = funcs + [functools.partial(_parse_module, package=pkg, verbose=verbose)]
    return module if module.origin else None, funcs


def _parse_pyfile(module, first_only):
    """Method for parsing python source code files to look for prints"""
    if isinstance(module, ImportException):
        return ([], module)

    prints = []
    encoding = "utf-8"
    # First two lines of Python source code have to be ASCII compatible
    # PEP-8, PEP-263, PEP-3120
    for mod_file in module.origin:
        with open(mod_file, "r", encoding="utf-8") as file:
            for _ in range(2):  # Check 1st two lines
                try:
                    found = re.search(ENCODING_CAPTURE, file.readline())
                except Exception as exc:  # pragma: no cover
                    raise exc
                if found:
                    encoding = found.group(1)
                    break

        with open(mod_file, "r", encoding=encoding) as file:
            parsed = ast.parse(file.read())
            clear = True
            name = ""
            if mod_file.endswith("__init__.py") or mod_file.endswith("__main__.py"):
                name = f".{mod_file[-11:-3]}"  # pragma: no cover
            for node in ast.walk(parsed):
                if node.__dict__.get("id") == "print":
                    clear = False

                    prints.append(
                        (
                            f"[{module.name}{name}] Line: {node.lineno}",
                            True,
                        )
                    )
                    if first_only:
                        return (prints, None)
            if clear:
                prints.append(
                    (
                        f"[CLEAR]:[{module.name}{name}]",
                        False,
                    )
                )
    return (prints, None)


class PackageFinder:
    """Class responsible for finding all packages and handling multiprocessing"""

    processes = []
    results = []

    def __init__(self, threads):  # pragma: no cover
        self.pool = Pool(threads)

    def err_callback(self, exc):  # pragma: no cover
        """Error callback from searching module"""
        self.results.append(exc)

    def callback(self, res):  # pragma: no cover
        """Callback from finding module"""
        self.results.append(res[0])
        for func in res[1]:
            proc = self.pool.apply_async(
                func, callback=self.callback, error_callback=self.err_callback
            )
            self.processes.append(proc)

    def packages_iter(self, packages: tuple, verbose: bool = False):
        """Iterate over all provided subpackages"""
        for package in packages:
            func = functools.partial(_parse_module, package=package, verbose=verbose)
            proc = self.pool.apply_async(
                func, callback=self.callback, error_callback=self.err_callback
            )
            self.processes.append(proc)

        while len(self.processes) > 0:
            for job in list(self.processes):
                if job.ready():
                    self.processes.remove(job)
                    res = self.results.pop()
                    if res:
                        yield res

    def run(self, first_only, packages, verbose):
        """Find print statements and potential exceptions from selected packages"""
        prints = []
        exceptions = []

        func = functools.partial(_parse_pyfile, first_only=first_only)
        for module in self.packages_iter(packages, verbose):
            found, exception = func(module)
            if found:
                prints = prints + found
            elif exception:
                exceptions.append(exception)
            if any(printed for _, printed in found) and first_only:
                break
        self.pool.terminate()
        self.pool.join()
        return (
            prints,
            exceptions,
        )


def detect_prints(
    packages: tuple,
    first_only: bool = False,
    verbose: bool = False,
    pool_threads: int = 1,
) -> Tuple[list, list]:  # pragma: no cover
    """Detect print statements from packages found by _get_subpackages"""
    logging.log(
        "Starting analysis, depending on package complexity, this may take a few seconds...",
        logging.INFO,
    )

    pkg_finder = PackageFinder(pool_threads)
    return pkg_finder.run(first_only, packages, verbose)
