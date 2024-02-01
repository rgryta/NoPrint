"""
Logging setup for NoPrint
"""

import os
import sys

from pathlib import Path
from functools import lru_cache
from importlib.machinery import ModuleSpec, PathFinder

from noprint.exceptions import ParentModuleNotFoundException


def _get_module_search_path(module: ModuleSpec):
    """Get path where submodules are located"""
    pkg_path = module.submodule_search_locations
    if isinstance(pkg_path, list):
        pkg_path = pkg_path[0]
    else:  # pragma: no cover
        # Patch for _NamespacePath in Python3.7
        pkg_path = pkg_path._path[0]  # pylint: disable=protected-access
    return pkg_path


def _get_module_location(module: ModuleSpec):
    """Get location of the module"""
    if module.has_location:
        path = Path(module.origin)
        if path.name == "__init__.py":
            path = path.parents[1]
        else:
            path = path.parents[0]
    else:
        path = Path(_get_module_search_path(module))
        path = path.parent
    return str(path)


@lru_cache(maxsize=None)
def _find_parent_dir(package: str, in_cwd: bool) -> str:
    """Get location of submodule"""
    paths = sys.path.copy()
    if in_cwd:
        paths.insert(0, os.getcwd())

    module = PathFinder.find_spec(package, path=paths)

    if module is None:
        raise ParentModuleNotFoundException(f"Parent module not found for package {package}, [in_cwd: {in_cwd}]")
    path = _get_module_location(module)

    return path


def _next_path(path, submodules):
    for i, _ in enumerate(submodules.split(".")):
        dir_check = submodules.rsplit(".", maxsplit=i)[0]
        dir_check = os.path.join(path, dir_check)
        if os.path.isdir(dir_check):
            return dir_check
    return None


def _package_to_dir(path, submodules):
    package_path = None
    for _ in enumerate(submodules.split(".")):
        package_path = _next_path(path, submodules)
        if package_path:
            submodules = submodules[len(package_path) - len(path) :]
            if os.path.isdir(package_path):
                path = package_path
        else:
            return None
    return package_path


class Module:
    """Module class to use instead of official classes which import main package when submodule is provided"""

    _origin = None
    _name = None

    _parent_loc = None  # Location of main parent pacakge (e.g. main.submodule.sm will return main)
    _package = None

    _search_path = None

    def __init__(self, package: str, in_cwd: bool = True):
        self._package = package
        try:
            ppackage = package.split(".", maxsplit=1)[0]
            self._parent_loc = _find_parent_dir(package=ppackage, in_cwd=in_cwd)
        except Exception as exc:
            raise ParentModuleNotFoundException(exc) from exc

    @property
    def origin(self):
        """Function to recover module origin - file paths"""
        if self._origin is None:
            path = Path(self._parent_loc)
            for step in self._package.split(".")[0:-1]:
                path = os.path.join(path, step)
            # SRC path
            cur_package = self._package.rsplit(".", maxsplit=1)[-1]
            self._origin = []

            # Check if module with submodules
            if os.path.isdir(os.path.join(path, cur_package)):
                path = os.path.join(path, cur_package)
                candidates = ["__init__.py", "__main__.py"]
                for candidate in candidates:
                    if os.path.isfile(os.path.join(path, candidate)):
                        self._origin.append(os.path.join(path, candidate))
            else:
                if os.path.isfile(os.path.join(path, f"{cur_package}.py")):
                    self._origin.append(os.path.join(path, f"{cur_package}.py"))
        return self._origin

    @property
    def name(self):
        """Recover package name"""
        return self._package

    @property
    def search_path(self):
        """Get path to use for searching submodules"""
        if self._search_path is None:
            self._search_path = _package_to_dir(self._parent_loc, self._package)
        if self._search_path and os.path.isdir(self._search_path):
            return self._search_path
        return None

    def __eq__(self, other):
        if isinstance(other, Module):
            pkg_check = self.name == other.name
            ppath_check = self._parent_loc == other._parent_loc
            return all([pkg_check, ppath_check])
        return False
