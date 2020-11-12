#! /usr/bin/env bash

set -e


HERE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DIS_DIR=${HERE_DIR}/../dist

rm -f $DIS_DIR/*



# PiPy
rm -fr ${DIS_DIR}/*
python3 setup.py sdist bdist_wheel
python3 -m twine upload -u __token__ -p $PYPI_TOKEN --repository pypi ${DIS_DIR}/*



# Conda
cd ${HERE_DIR}/..
conda-build --user informaticslab -c conda-forge .