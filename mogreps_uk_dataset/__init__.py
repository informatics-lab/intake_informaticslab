
# fmt: off
# autopep8: off
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions



from .datasources.mogreps_uk import MogrepsUkDataSource
import os
# fmt: on
# autopep8: on
