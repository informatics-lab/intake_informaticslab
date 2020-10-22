# Met Office datasets intake driver and catalogue

...


# Building the package

## PyPI

```shell
#user=informaticslab
python3 setup.py sdist bdist_wheel
python3 -m twine upload -u informaticslab --repository testpypi dist/*



```

## Anaconda

```shell
conda-build --user informaticslab -c conda-forge .
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



So tips building conda stuff. I said it took ages to build the env and didn't wat to keep doing that for testing the build. Answers:
```

Wolf Vollprecht @wolfv 15:08
you can point the shell to your workdir and run the conda_build.sh from that folder
and you can source build_env.sh to get into the buidl env, then conda deactivate to get into the host env and install / modify packages in there
the workdir is shown in the error message after conda build failed
otherwise you might want to try conda mambabuild ... which is included in boa to see if that could help speed up your build env provisioning


Otherwise, you might want to try to use conda debug instead of conda build in the first place. This only creates the environment setup but doesn't start the build.
```