from xarray import Dataset
import numpy as np


def test_from_cat():
    import intake
    import os
    cat_path = os.path.join(os.path.dirname(__file__), "../intake_informaticslab/cats/ukv_timeseries_cat.yaml")
    cat = intake.open_catalog(cat_path)
    ds = cat.ukv_daily_timeseries.read_chunked()
    assert isinstance(ds, Dataset)
    for var in ds.data_vars:
        da = ds[var]
        assert len(da.shape) == 3  # 3d field time x X x Y
        assert np.product(da.shape) > 0  # non zero size
