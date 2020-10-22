#! /usr/bin/env bash

python -m pip install --user --upgrade setuptools wheel
python3 -m pip install --user --upgrade twine
conda install conda-build anaconda-client