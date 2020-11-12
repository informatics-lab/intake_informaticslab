from datetime import date
from xarray import Dataset
import numpy as np


def test_import():
    from met_office_datasets.datasources.aq_datasource import AQDataset


def test_init():
    from met_office_datasets.datasources.aq_datasource import AQDataset
    import datetime
    ds = AQDataset(
        start_cycle="20200101T0000Z",
        end_cycle="20201108T0000Z",
        diagnostics=['o3', 'no2', 'pm10', 'pm2p5', 'so2'],
        model='aqum_hourly',
        cycle_frequency="1H",
        dims=["time", "projection_y_coordinate", "projection_x_coordinate"],
        static_coords={
            "projection_y_coordinate": {
                "data": {"start": -184000, "stop": 1222000, "num": 704},
                "attrs":
                {
                    "axis": "y",
                    "units": "m",
                    "standard_name": "projection_y_coordinate"
                }
            },
            "projection_x_coordinate": {
                "data": {"start": -238000, "stop": 856000, "num": 548},
                "attrs":
                {
                    "axis": "x",
                    "units": "m",
                    "standard_name": "projection_x_coordinate"
                }
            }
        },
        storage_options={
            "data_protocol": "abfs",
            "url_prefix": "covid19-response",
            "account_name": "metdatasa",
            "credential": None
        })


def test_from_cat():
    import intake
    import os
    cat_path = os.path.join(os.path.dirname(__file__), "../met_office_datasets/air_quality_cat.yaml")
    cat = intake.open_catalog(cat_path)
    ds = cat.air_quality_hourly.read_chunked()
    assert isinstance(ds, Dataset)
    assert len(ds.data_vars) == 5
    for var in ds.data_vars:
        da = ds[var]
        assert len(da.shape) == 3  # 3d field time x X x Y
        assert np.product(da.shape) > 0  # non zero size
