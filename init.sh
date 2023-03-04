#!/bin/bash
cd "$(dirname "$0")"

mkdir venv && \
python3 -m venv ./venv && \
. venv/bin/activate && \
pip install --editable . && \
pip install -r ./requirements_dev.txt