def test_import():
    from met_office_datasets import MetOfficeDataSource


def test_init():
    from met_office_datasets import MetOfficeDataSource

    ds = MetOfficeDataSource(
        start_cycle="20200101T0000Z",
        end_cycle="20200101T0000Z",
        cycle_frequency="1H",
        forecast_extent="1H",
        model="mo-atmospheric-mogreps-uk",
        diagnostics=["temperature_at_screen_level"],
        storage_options={
            'data_protocol': 'file',
            'url_prefix': '/tmp/',
        }
    )


def test_get_some_data():
    import xarray as xr
    from met_office_datasets import MetOfficeDataSource

    ds = MetOfficeDataSource(
        start_cycle="20200101T0000Z",
        end_cycle="20200101T0000Z",
        cycle_frequency="1H",
        forecast_extent="1H",
        model="mo-atmospheric-mogreps-uk",
        diagnostics=["temperature_at_screen_level"],
        storage_options={
            'data_protocol': 'file',
            'url_prefix': '/tmp/',
        }
    )
    data = ds.read_chunked()
    assert isinstance(data, xr.Dataset) == True
