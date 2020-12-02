from logging import error


def test_import():
    from intake_informaticslab import MetOfficeDataSource


def test_init():
    from intake_informaticslab import MetOfficeDataSource

    ds = MetOfficeDataSource(
        start_cycle="20200101T0000Z",
        end_cycle="20200101T0000Z",
        cycle_frequency="1H",
        forecast_extent="1H",
        model="mo-atmospheric-mogreps-uk",
        dimensions=[
            "forecast_reference_time",
            "forecast_period",
            "realization",
            "projection_y_coordinate",
            "projection_x_coordinate",
        ],
        diagnostics=["temperature_at_screen_level"],
        static_coords={
            "realization": {"data": [0, 1, 2]},
            "projection_y_coordinate": {"data": {"start": 100, "stop": 200, "num": 10}},
            "projection_x_coordinate": {"data": {"start": 100, "stop": 200, "num": 10}},
        },
        storage_options={
            "data_protocol": "file",
            "url_prefix": "/tmp/",
        },
    )


def test_licence_not_accepted():
    from intake_informaticslab import MetOfficeDataSource, LicenceNotExceptedError

    error_raised = False
    license = "My Licence"
    try:
        ds = MetOfficeDataSource(
            start_cycle="20200101T0000Z",
            end_cycle="20200101T0000Z",
            cycle_frequency="1H",
            forecast_extent="1H",
            model="mo-atmospheric-mogreps-uk",
            dimensions=[
                "forecast_reference_time",
                "forecast_period",
                "realization",
                "projection_y_coordinate",
                "projection_x_coordinate",
            ],
            diagnostics=["temperature_at_screen_level"],
            static_coords={
                "realization": {"data": [0, 1, 2]},
                "projection_y_coordinate": {"data": {"start": 100, "stop": 200, "num": 10}},
                "projection_x_coordinate": {"data": {"start": 100, "stop": 200, "num": 10}},
            },
            storage_options={
                "data_protocol": "file",
                "url_prefix": "/tmp/",
            },
            license=license
        )
    except LicenceNotExceptedError as e:
        assert license in str(e)
        error_raised = True

    assert error_raised


def test_licence_accepted():
    from intake_informaticslab import MetOfficeDataSource, LicenceNotExceptedError

    error_raised = False
    license = "My Licence"
    try:
        ds = MetOfficeDataSource(
            start_cycle="20200101T0000Z",
            end_cycle="20200101T0000Z",
            cycle_frequency="1H",
            forecast_extent="1H",
            model="mo-atmospheric-mogreps-uk",
            dimensions=[
                "forecast_reference_time",
                "forecast_period",
                "realization",
                "projection_y_coordinate",
                "projection_x_coordinate",
            ],
            diagnostics=["temperature_at_screen_level"],
            static_coords={
                "realization": {"data": [0, 1, 2]},
                "projection_y_coordinate": {"data": {"start": 100, "stop": 200, "num": 10}},
                "projection_x_coordinate": {"data": {"start": 100, "stop": 200, "num": 10}},
            },
            storage_options={
                "data_protocol": "file",
                "url_prefix": "/tmp/",
            },
            license=license,
            licence_accepted=True
        )
    except LicenceNotExceptedError as e:
        error_raised = True

    assert not error_raised


def test_licence_accepted_wrong():
    from intake_informaticslab import MetOfficeDataSource, LicenceNotExceptedError

    error_raised = False
    license = "My Licence"
    try:
        ds = MetOfficeDataSource(
            start_cycle="20200101T0000Z",
            end_cycle="20200101T0000Z",
            cycle_frequency="1H",
            forecast_extent="1H",
            model="mo-atmospheric-mogreps-uk",
            dimensions=[
                "forecast_reference_time",
                "forecast_period",
                "realization",
                "projection_y_coordinate",
                "projection_x_coordinate",
            ],
            diagnostics=["temperature_at_screen_level"],
            static_coords={
                "realization": {"data": [0, 1, 2]},
                "projection_y_coordinate": {"data": {"start": 100, "stop": 200, "num": 10}},
                "projection_x_coordinate": {"data": {"start": 100, "stop": 200, "num": 10}},
            },
            storage_options={
                "data_protocol": "file",
                "url_prefix": "/tmp/",
            },
            license=license,
            licence_accepted="No I Don't"
        )
    except LicenceNotExceptedError as e:
        error_raised = True

    assert error_raised


def test_get_some_data():
    import xarray as xr
    from intake_informaticslab import MetOfficeDataSource

    ds = MetOfficeDataSource(
        start_cycle="20200101T0000Z",
        end_cycle="20200101T0000Z",
        cycle_frequency="1H",
        forecast_extent="1H",
        model="mo-atmospheric-mogreps-uk",
        dimensions=[
            "forecast_reference_time",
            "forecast_period",
            "realization",
            "projection_y_coordinate",
            "projection_x_coordinate",
        ],
        diagnostics=["temperature_at_screen_level"],
        static_coords={
            "realization": {"data": [0, 1, 2]},
            "projection_y_coordinate": {"data": {"start": 100, "stop": 200, "num": 10}},
            "projection_x_coordinate": {"data": {"start": 100, "stop": 200, "num": 10}},
        },
        storage_options={
            "data_protocol": "file",
            "url_prefix": "/tmp/",
        },
    )
    data = ds.read_chunked()
    assert isinstance(data, xr.Dataset) == True
