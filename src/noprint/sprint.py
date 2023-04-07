"""
Module responsible for finding print statements in python modules
"""
import os
import re
import ast
import pkgutil
import functools
import concurrent.futures as cc
import time
from typing import Union, Tuple
from pathlib import Path
from importlib.machinery import ModuleSpec
from multiprocessing import SimpleQueue, Manager
from multiprocessing.pool import Pool

import noprint.logger as logging

from noprint import ENCODING_CAPTURE
from noprint.module import Module
from noprint.exceptions import ImportException, ParentModuleNotFoundException


def _get_subpackages(
    package: str, verbose: bool = False
) -> Union[ModuleSpec, ImportException]:
    """Grab all packages and subpackages"""
    # Patch out statements from __init__
    try:
        module = Module(package)
    except ParentModuleNotFoundException as exc:
        return ImportException(exc), None
    system_module = None
    try:
        system_module = Module(package, in_cwd=False)
    except ParentModuleNotFoundException:  # pragma: no cover
        pass

    if not module:
        return (
            ImportException(
                f"Module [{package}] is not present in current environment, directory or PYTHONPATH"
            ),
            None,
        )

    if not system_module and verbose:
        logging.log(f"Module [{package}] is not installed", logging.WARNING)
    elif module != system_module and verbose and len(system_module.origin) > 0:
        logging.log(
            f"Module [{package}] is overshadowing installed module", logging.WARNING
        )

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
    sub_pkgs = list(set(candidates) | set(sub_pkgs))

    mod = None
    func = []
    for pkg in sub_pkgs:
        func = func + [
            functools.partial(_get_subpackages, package=pkg, verbose=verbose)
        ]
    if module.origin:
        mod = module
    return mod, func


class PackageFinder:
    executor = None
    sq = None

    l = []
    res = []

    def __init__(self):
        # self.executor = MyExecutor()
        self.executor = cc.ProcessPoolExecutor()
        self.sq = SimpleQueue()
        self.mg = Manager()

        self.p = Pool(24)

    def err(self, check):
        import traceback

        traceback.print_exc()

    def callback(self, res):
        self.res.append(res[0])
        for func in res[1]:
            res = self.p.apply_async(
                func, callback=self.callback, error_callback=self.err
            )
            self.l.append(res)

    def packages_iter(self, packages: tuple, verbose: bool = False):
        """Iterate over all provided subpackages"""
        for package in packages:  # pragma: no cover
            func = functools.partial(_get_subpackages, package=package, verbose=verbose)
            res = self.p.apply_async(
                func, callback=self.callback, error_callback=self.err
            )
            self.l.append(res)

        while len(self.l) > 0:
            for job in list(self.l):
                if job.ready():
                    self.l.remove(job)
                    res = self.res.pop()
                    if res:
                        yield res


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
    logging.log(
        "Starting analysis, depending on package complexity, this may take a few seconds...",
        logging.INFO,
    )
    pf = PackageFinder()
    pkgs = [x for x in pf.packages_iter(packages, verbose)]
    with Pool(pool_threads) as pool:
        for found, exception in pool.imap(func, pkgs):
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
