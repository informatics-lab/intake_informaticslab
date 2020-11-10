from .dataset import MODataset
import xarray as xr
import numpy as np
import pandas as pd
from .utils import datetime_to_iso_str
from io import BytesIO


class AQDataset(MODataset):

    def __init__(self, storage_options):

        start_cycle = "20200101T0000Z"
        end_cycle = "20200105T0000Z"
        model = 'aqum_hourly'
        diagnostics = ['o3']
        super().__init__(start_cycle, end_cycle, model, diagnostics, cycle_freq='1H', start_lead_time=None, end_lead_time="126H", lead_time_freq="None",  **storage_options)

    @property
    def chunks(self):
        static_coords = self.static_coords
        chunks = {name: static_coords[name].shape[0] for name in static_coords.keys()}
        assert self.cycle_freq in ['1H', '1D']
        if self.cycle_freq == '1H':
            time_chunks = 24
        elif self.cycle_freq == '1D':
            time_chunks = 1
        else:
            raise RuntimeError(f"Don't know how to deal with cycle_freq {cycle_freq} for chunking")

        chunks.update({'time': time_chunks})
        return chunks

    @property
    def dynamic_coords(self):
        dynamic_coords_data = {
            "time": pd.date_range(
                start=self.start_cycle, end=self.end_cycle, freq=self.cycle_freq
            )
        }
        return {
            name: xr.Variable(dims=(name,), data=data)
            for name, data in dynamic_coords_data.items()
        }

    @property
    def dims(self):
        return (
            "time",
            "projection_y_coordinate",
            "projection_x_coordinate",
        )

    @property
    def static_coords(self):
        static_coords = self._create_grid_coords()
        return static_coords

    @staticmethod
    def _create_grid_coords():
        GRID_DEFINITION = {"x": (-238000, 856000, 548), "y": (-184000, 1222000, 704)}

        coords = {}
        for axis in ("x", "y"):
            name = f"projection_{axis}_coordinate"
            minval, maxval, npts = GRID_DEFINITION[axis]
            data = np.linspace(minval, maxval, npts, endpoint=True)
            coords[name] = xr.Variable(
                dims=(name,),
                data=data,
                attrs={
                    "axis": axis,
                    "units": "m",
                    "standard_name": name,
                },
            )
        return coords

    def _get_blob_url(
        self, diagnostic, time=None
    ):
        """Return the URL of a forecast file."""
        # model and diagnostic are strings
        # time (datetime.datetime)

        # convert all to strings
        time_str = datetime_to_iso_str(time).split('T')[0]

        # 'covid-response-ds/metoffice_aqum_hourly/o3/aqum_hourly_o3_20200101.nc'

        obj_path = (
            f"metoffice_{self.model}/{diagnostic}/{self.model}_{diagnostic}_{time_str}.nc"
        )
        obj_path = f"{self.url_prefix}/{obj_path}"
        return f"{self.data_protocol}://{obj_path}"

    def _zstore_loader(self, attrs):
        time = attrs["time"]
        diag = attrs["variable_name"]

        time = pd.to_datetime(np.datetime64(time, "ns"))

        # https://metdatasa.blob.core.windows.net/covid19-response/metoffice_ukv_daily/snow_max/ukv_daily_snow_max_20200101.nc
        url = self._get_blob_url(
            diagnostic=diag, time=time
        )

        try:
            data = self._read_from_url(url)
            data = xr.open_dataset(BytesIO(data))
            data = self._extract_data_as_dataarray(data)
            return data.values
        except FileNotFoundError:
            return None

    @staticmethod
    def _extract_data_as_dataarray(dataset):
        # coords in all datasets
        REQUIRED_COORD_VARS = [
            "time",
            "projection_y_coordinate",
            "projection_x_coordinate",
            "forecast_reference_time",
            "forecast_day"
        ]

        # coords only in some datasets
        VERTICAL_COORD_VARS = ["height", "depth", "pressure"]

        # variables that are not in coords or dims (including 'bnds' in dims)
        # but in all datasets
        REQUIRED_NON_COORD_DIM_VARS = [
            "lambert_azimuthal_equal_area",
            "projection_y_coordinate_bnds",
            "projection_x_coordinate_bnds",
            "transverse_mercator",
            "experiment_number"
        ]

        # vars that are not coords/dims but are optional
        TIME_BOUND_VARS = ["time_bnds", "forecast_period_bnds"]

        # also has 'depth_bnds' optionally..
        # need to figure out which variable is the data variable
        NON_DATA_VARS = (
            REQUIRED_COORD_VARS
            + VERTICAL_COORD_VARS
            + REQUIRED_NON_COORD_DIM_VARS
            + TIME_BOUND_VARS
            + ["depth_bnds"]
        )

        data_var = list(set(dataset.variables) - set(NON_DATA_VARS))
        if len(data_var) > 1:
            raise RuntimeError("Expected to find only 1 data variable")
        data_var = data_var[0]
        return dataset[data_var]