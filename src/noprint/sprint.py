"""
Module responsible for finding print statements in python modules
"""
import os
import re
import ast
import pkgutil
import functools
import contextvars
from pathlib import Path
from multiprocessing.pool import Pool

import noprint.logger as logging

from noprint import ENCODING_CAPTURE
from noprint.module import Module
from noprint.exceptions import ImportException, ParentModuleNotFoundException


packages = contextvars.ContextVar("packages", default=[])
mt_threads = contextvars.ContextVar("mt_threads", default=1)
log_lvl = contextvars.ContextVar("log_lvl", default=logging.WARNING)
first_only = contextvars.ContextVar("first_only", default=False)
verbose = contextvars.ContextVar("verbose", default=False)
very_verbose = contextvars.ContextVar("very_verbose", default=False)


def _get_module(package):
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

    if not system_module and verbose.get():
        logging.log(
            f"Module [{package}] is not installed", logging.WARNING
        )  # pragma: no cover
    elif (
        verbose.get()
        and system_module
        and module != system_module
        and len(system_module.origin) > 0
    ):  # pragma: no cover
        logging.log(
            f"Module [{package}] is overshadowing installed module", logging.WARNING
        )

    return module


def _get_subpackages(package, module):
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
    if isinit and candidates_missing and verbose.get():  # pragma: no cover
        for candidate in candidates_missing:
            logging.log(f"Module [{candidate}] has no __init__.py", logging.WARNING)
    # Patch missing submodules
    return list(set(candidates) | set(sub_pkgs))


def _parse_module(package: str):
    """Grab all packages and subpackages"""
    module = _get_module(package)

    sub_pkgs = _get_subpackages(package, module)

    funcs = []
    for pkg in sub_pkgs:
        funcs = funcs + [functools.partial(_parse_module, package=pkg)]
    return module if module.origin else None, funcs


def _parse_pyfile(module):
    """Method for parsing python source code files to look for prints"""
    if isinstance(module, ImportException):
        logging.log(module.args[0], logging.CRITICAL)
        return 2

    encoding = "utf-8"
    status = 0
    # First two lines of Python source code have to be ASCII compatible
    # PEP-8, PEP-263, PEP-3120
    for mod_file in module.origin:
        with open(mod_file, "r", encoding="utf-8") as file:
            for _ in range(2):  # Check 1st two lines
                try:
                    found = re.search(ENCODING_CAPTURE, file.readline())
                # pylint: disable=broad-exception-caught
                except Exception as exc:  # pragma: no cover
                    logging.log(exc.args[0], logging.CRITICAL)
                    return 2
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
                    status = 1
                    if verbose.get():  # pragma: no cover
                        logging.log(
                            f"[{module.name}{name}] Line: {node.lineno}", log_lvl.get()
                        )

                    if first_only.get():  # pragma: no cover
                        return status
            if clear and very_verbose.get():
                logging.log(
                    f"[CLEAR]:[{module.name}{name}]", logging.INFO
                )  # pragma: no cover
    return status


class PackageFinder:
    """Class responsible for finding all packages and handling multiprocessing"""

    processes = []
    results = []

    def __init__(self):  # pragma: no cover
        self.pool = Pool(mt_threads.get())

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

    def packages_iter(self):
        """Iterate over all provided subpackages"""
        for package in packages.get():
            func = functools.partial(_parse_module, package=package)
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

    def run(self):
        """Find print statements and potential exceptions from selected packages"""
        results = []

        for module in self.packages_iter():
            res = _parse_pyfile(module)
            results.append(res)
            if res >= 1 and first_only.get():  # pragma: no cover
                break
        self.pool.terminate()
        self.pool.join()
        return max(results)


def detect_prints() -> int:  # pragma: no cover
    """Detect print statements from packages found by _get_subpackages"""
    # pylint: disable=unnecessary-lambda-assignment
    get_var = lambda name, ctx: [var.get() for var in iter(ctx) if var.name == name][0]

    ctx = contextvars.copy_context()

    packages.set(get_var("packages", ctx))
    mt_threads.set(get_var("mt_threads", ctx))
    log_lvl.set(get_var("log_lvl", ctx))
    first_only.set(get_var("first_only", ctx))
    verbose.set(get_var("verbose", ctx))
    very_verbose.set(get_var("very_verbose", ctx))

    logging.log(
        "Starting analysis, depending on package complexity, this may take a few seconds...",
        logging.INFO,
    )
    pkg_finder = PackageFinder()
    return pkg_finder.run()
