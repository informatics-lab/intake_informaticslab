# fmt: off
# autopep8: off
from ._version import get_versions

__version__ = get_versions()['version']
del get_versions



import os

import intake

from .datasources import (LicenseNotExceptedError, MergedMetOfficeDataSource,
                          MetOfficeDataSource)

CATALOG_DIR = os.path.join(os.path.dirname(__file__), 'cats')

mogreps_cat = intake.open_catalog(os.path.join(CATALOG_DIR, 'mogreps_cat.yaml'))
aq_cat = intake.open_catalog(os.path.join(CATALOG_DIR, 'air_quality_cat.yaml'))
ukv_single_timeseries = intake.open_catalog(os.path.join(CATALOG_DIR, 'ukv_timeseries_cat.yaml'))

cat = intake.catalog.Catalog.from_dict(
    {
        'air_quality': aq_cat,
        'weather_forecasts': mogreps_cat,
        'weather_continuous_timeseries': ukv_single_timeseries

    }, name="Met Office Datasets")

# fmt: on
# autopep8: on
