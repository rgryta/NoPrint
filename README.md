<p align="center"><a href="https://rgryta.github.io/project/noprint"><img src="https://raw.githubusercontent.com/rgryta/NoPrint/main/docs/logo.png"  width="30%" height="40%"></a></p>
<h2 align="center">NoPrint</h2>
<p align="center">
<a href="https://github.com/rgryta/NoPrint/actions/workflows/main.yml"><img alt="Python package" src="https://github.com/rgryta/NoPrint/actions/workflows/main.yml/badge.svg?branch=main"></a>
<a href="https://pypi.org/project/noprint/"><img alt="PyPI" src="https://img.shields.io/pypi/v/noprint"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://github.com/PyCQA/pylint"><img alt="pylint" src="https://img.shields.io/badge/linting-pylint-yellowgreen"></a>
<a href="https://github.com/rgryta/NoPrint"><img alt="NoPrint" src="https://img.shields.io/badge/NoPrint-enabled-blueviolet"></a>
</p>

## About

Do not allow prints in your python code anymore. Official repository of NoPrint package. Packages are scanned recursively.

## Output readout

Visible always:
 - Critical info - if import of one of your modules results with an exception (or is missing - maybe you mistyped your package?).
 - Final result (success, prints detected or critical error)

Verbosity options for `-v`:
 - Outputs which modules contain print statements at which lines
 - Warning when any of your submodules are missing `__init__.py` files (reported always as warnings) 
 - Receive a warning if one of packages that's being analysed is out of system's scope - it will still be scanned, but that "package" is not reachable outside of that directory, these are e.g. `tests` directories
 - Receive a warning if one of your packages is overshadowing a package available on system/environment level, e.g. if you have requested to analyse your `test` directory, but Python already has an internal package called `test`

Verbosity options for `-vv` (or `-v -v` on older Python versions):
 - All the options from `-v`
 - NoPrint will tell you specifically which of your submodules are clear of print statements

## Requirements

There's ***NONE!*** You can use this package to your heart's content. Unless you'd like to develop for it, for this you'll need Black, Pylint and Pytest along with Pytest-cov.

## Installation

Pull straight from this repo to install manually or just use pip: `pip install noprint` will do the trick.

## Usage

### Use as command:
```bash
usage: NoPrint [-h] [-e] [-f] [-v] [--version] packages [packages ...] [-m [MULTI]]

Do not allow prints in your code.

positional arguments:
  packages              which packages/modules to check, syntax: <package>[.<module> ...], e.g. noprint or noprint.cli

options:
  -h, --help            show this help message and exit
  -e, --error-out       exit with error when print is found (by default only warnings are shown)
  -f, --first-only      finish on first print found
  -v, --verbose         provide more analysis information (use multiple v's to increase logging level)
  -m [MULTI], --multi [MULTI]
                        set how many threads to use
  --version             show program's version number and exit

Thank you for using NoPrint
```

### Multithreading

Provide number of threads after `-m` parameter. Default's to 1 if not provided or provided without specific number. If 0 or less is given then it will use number of available vCPUs reported by multiprocessing library.

### Example in Makefile:
```bash
(venv) root@/DummyProject# make test
{ \
        . venv/bin/activate && \
        noprint -evvm 0 tp && \
        echo "Finished!" ; \
}
[CLEAR]:[tp.exceptions]
[CLEAR]:[tp.logger]
[CLEAR]:[tp.cli]
[ERROR]:[tp] Line: 4
[ERROR]:[tp.submodule] Line: 20
[ERROR]:Print statements detected
make: *** [Makefile:4: test] Error 1
```

This package performs recursive tests on itself before being merged - you can check suggested usage in Makefile. 

## Development

If you'd like to develop for this package (for some reason) then it's rather straightforward. On Windows start `init.bat` command (WSL2 required). This will install a local WSL2 image with small Ubuntu environment and set up virtual environment for you. If you're already using Unix-based system, you can just use `init.sh` as that will create Python virtual environment.

Before creating Pull Request, make sure that your tests are passing. This is a small package, so I want to maintain 100% coverage - `# pragma: no cover` is only allowed in very specific scenarios (like single line method wrapper).

## Want to show off?

Feel free to drop this badge into your repo. Glad to have you onboard.

```md
<a href="https://github.com/rgryta/NoPrint"><img alt="NoPrint" src="https://img.shields.io/badge/NoPrint-enabled-blueviolet"></a>
```
