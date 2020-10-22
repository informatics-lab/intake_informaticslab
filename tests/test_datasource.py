import xarray as xr


def test_import():
    from metoffice_datasets import MogrepsUkDataSource


def test_init():
    from metoffice_datasets import MogrepsUkDataSource

    ds = MogrepsUkDataSource()


def test_get_some_data():
    from metoffice_datasets import MogrepsUkDataSource

    ds = MogrepsUkDataSource()
    data = ds.read()
    assert isinstance(data, xr.Dataset) == True
