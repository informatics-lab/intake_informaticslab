# python-conda-package-template

Template for building Python packages that can be easily bundled as Anaconda packages, too

# Usage

To use this package, when creating the new repository for your project, select this project as the template.
Then, replace all occurrences of "PACKAGENAME", "URL", "GIT_URL", and other filler values in `setup.py` and `meta.yaml`.
Set version numbers as needed in `PACKAGENAME/__init__.py` and `meta.yaml`, and add your code where applicable.

# Building your package

## PyPI

```shell
python setup.py install
```

## Anaconda

```shell
conda build --python {PYTHON_VERSION} meta.yaml
```

# Uploading your package

## PyPI

```shell
# ensure `twine` is install
pip install twine
# package source code
python setup.py sdist
twine upload dist/*
```

## Anaconda

```shell
# ensure conda-build and anaconda-client are installed
conda install conda-build anaconda-client
# build package for a specific python version
conda build --python {PYTHON_VERSION} meta.yaml
# upload to Anaconda Cloud
cd $HOME/miniconda3/conda-bld/
anaconda upload */PACKAGENAME-VERSION_*.tar.bz2
```

# Installing your package

After uploading to your repository of interest, you should be able to download and install your package according to the tools for that repository.

## PyPI

```shell
pip install PACKAGENAME
```

## Anaconda

```shell
conda install PACKAGENAME
```
