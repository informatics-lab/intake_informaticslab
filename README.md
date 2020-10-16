# python-conda-package-template

...


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
anaconda upload */mogreps_uk_dataset-VERSION_*.tar.bz2
```

# Installing your package

After uploading to your repository of interest, you should be able to download and install your package according to the tools for that repository.

## PyPI

```shell
pip install mogreps_uk_dataset
```

## Anaconda

```shell
conda install mogreps_uk_dataset
```
