import xarray as xr


def test_import():
    from mogreps_uk_dataset import MogrepsUkDataSource


def test_init():
    from mogreps_uk_dataset import MogrepsUkDataSource

    ds = MogrepsUkDataSource()


def test_get_some_data():
    from mogreps_uk_dataset import MogrepsUkDataSource

    ds = MogrepsUkDataSource()
    data = ds.read()
    assert isinstance(data, xr.Dataset) == True
