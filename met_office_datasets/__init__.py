# fmt: off
# autopep8: off
from ._version import get_versions

__version__ = get_versions()['version']
del get_versions



import os

import intake

from .datasources import MetOfficeDataSource

mogreps_cat = intake.open_catalog(os.path.join(os.path.dirname(__file__), 'mogreps_uk_cat.yaml'))
aq_cat = intake.open_catalog(os.path.join(os.path.dirname(__file__), 'air_quality_cat.yaml'))
# fmt: on
# autopep8: on
