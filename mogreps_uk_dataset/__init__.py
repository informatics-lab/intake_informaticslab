# fmt: off
# autopep8: off
from ._version import get_versions

__version__ = get_versions()['version']
del get_versions



import os

from .datasources.mogreps_uk import MogrepsUkDataSource

# fmt: on
# autopep8: on
