import versioneer
from setuptools import setup, find_packages
from os import path

this_dir = path.abspath(path.dirname(__file__))
with open(path.join(this_dir, "README.md")) as f:
    long_description = f.read()

NAME = "mogreps_uk_dataset"

setup(
    name=NAME,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="DESCRIPTION",
    url="https://github.com/informatics-lab/mogreps_uk_dataset",
    author="Theo McCaie",
    author_email="theo.mccaie@informaticslab.co.uk",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.4',
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Natural Language :: English",
    ],
    packages=find_packages(),
    install_requires=["numpy>=1.11",
                      'dask>=1.0',
                      'xarray',
                      'zarr>=2',
                      'adlfs',
                      'h5netcdf>=0.8',
                      'adlfs',
                      'intake',
                      'toolz'],
    zip_safe=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    entry_points={
        'intake.catalogs': [
            f'met_office= {NAME}:cat'
        ]
    }
)
