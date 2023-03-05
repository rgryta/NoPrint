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

Do not allow prints in your python code anymore. Official repository of NoPrint package. Packages are scanned recursively. On top of that, this NoPrint will tell you if any of your submodules are missing `__init__.py` files (reported always as warnings).

## Installation

Pull straight from this repo to install manually or just use pip: `pip install noprint` will do the trick.

## Usage

Use as command:
```bash
(venv) root@/NoPrint# noprint --help
Usage: noprint [OPTIONS] [PACKAGES]...

  No prints are allowed!

Options:
  -f, --first-only  Exit on first print found.
  -e, --as-error    Exit with error when print is found (default is Warning).
  --help            Show this message and exit.
```

Example in Makefile:
```bash
(venv) root@/DummyProject# make test
{ \
        . venv/bin/activate && \
        noprint -e -f tp && \
        echo "Finished!" ; \
}
Print statements detected at:
[tp.submodule] Print at line 14 col 4
make: *** [Makefile:4: test] Error 1
```

This package performs recursive tests on itself before being merged - you can check suggested usage in Makefile. 

## Development

If you'd like to develop for this package (for some reason) then it's rather straightforward. On Windows start `init.bat` command (WSL2 required). This will install a local WSL2 image with small Ubuntu environment and set up virtual environment for you. If you're already using Unix-based system, you can just use `init.sh` that set's up Python virtual environment.

Before creating Pull Request, make sure that your tests are passing. This is a small package so I want to maintain 100% coverage - `# pragma: no cover` is only allowed in very specific scenarios (like single line method wrapper).

## Want to show off?

Feel free to drop this badge into your repo. Glad to have you onboard.

```md
<a href="https://github.com/rgryta/NoPrint"><img alt="NoPrint" src="https://img.shields.io/badge/NoPrint-enabled-blueviolet"></a>
```
