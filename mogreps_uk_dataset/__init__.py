
# fmt: off
# autopep8: off
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions



from .datasources.mogreps_uk import MogrepsUkDataSource
import os

import intake
cat = intake.open_catalog(os.path.join(os.path.dirname(__file__), 'mogreps_uk_cat.yaml'))
# fmt: on
# autopep8: on
