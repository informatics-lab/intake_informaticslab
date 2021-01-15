import datetime
from io import BytesIO

import numpy as np
import pandas as pd
import xarray as xr

from intake_informaticslab import __version__
from intake_informaticslab.datasources import MetOfficeDataSource

from .dataset import MODataset
from .utils import datetime_to_iso_str, remove_trailing_z


class TimeSeriesDatasource(MetOfficeDataSource):
    name = "met_office_ukv_timeseries"
    version = __version__

    def __init__(
        self,
        start_datetime,
        end_datetime,
        timestep,
        model,
        dimensions,
        diagnostics,
        static_coords,
        storage_options,
        license=None,
        metadata=None,
    ):

        if end_datetime.lower() == "latest":
            end_datetime = datetime_to_iso_str(
                (datetime.datetime.now() - datetime.timedelta(hours=48))
            )
        self.timestep = timestep
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime

        super().__init__(
            start_cycle=start_datetime,
            end_cycle=end_datetime,
            cycle_frequency=timestep,
            forecast_extent=None,
            model=model,
            dimensions=dimensions,
            static_coords=static_coords,
            diagnostics=diagnostics,
            storage_options=storage_options,
            license=None,
            metadata=metadata,
        )

    def _open_dataset(self):
        self._ds = TimeSeriesDataset(
            start_datetime=self.start_datetime,
            end_datetime=self.end_datetime,
            model=self.model,
            dims=self.dimensions,
            diagnostics=self.diagnostics,
            static_coords=self.static_coords,
            timestep=self.timestep,
            storage_options=self.storage_options,
        ).ds


class MetOfficeAQDataSource(MetOfficeDataSource):
    name = "met_office_aq"
    version = __version__

    def __init__(
        self,
        start_datetime,
        end_datetime,
        timestep,
        model,
        dimensions,
        diagnostics,
        static_coords,
        storage_options,
        aggregation=None,
        license=None,
        metadata=None,
    ):

        if end_datetime.lower() == "latest":
            end_datetime = datetime_to_iso_str(
                (datetime.datetime.now() - datetime.timedelta(hours=48))
            )

        self.aggregation = aggregation
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.timestep = timestep

        super().__init__(
            start_cycle=start_datetime,
            end_cycle=end_datetime,
            cycle_frequency=timestep,
            forecast_extent=None,
            model=model,
            dimensions=dimensions,
            static_coords=static_coords,
            diagnostics=diagnostics,
            storage_options=storage_options,
            license=license,
            metadata=metadata,
        )

    def _open_dataset(self):
        self._ds = AQDataset(
            start_datetime=self.start_datetime,
            end_datetime=self.end_datetime,
            model=self.model,
            dims=self.dimensions,
            diagnostics=self.diagnostics,
            static_coords=self.static_coords,
            timestep=self.timestep,
            storage_options=self.storage_options,
            aggregation=self.aggregation,
        ).ds


class SingleTimeDataset(MODataset):
    def __init__(
        self,
        start_datetime,
        end_datetime,
        model,
        dims,
        diagnostics,
        static_coords,
        timestep,
        storage_options,
        aggregation=None,
    ):

        # remove the 'Z' from the start/end points or xarray struggles...
        self.start_datetime = remove_trailing_z(start_datetime)
        self.end_datetime = remove_trailing_z(end_datetime)
        self.timestep = timestep
        self.aggregation = aggregation

        super().__init__(
            start_cycle=self.start_datetime,
            end_cycle=self.end_datetime,
            model=model,
            dims=dims,
            diagnostics=diagnostics,
            static_coords=static_coords,
            cycle_freq=timestep,
            start_lead_time=None,
            end_lead_time=None,
            lead_time_freq=None,
            **storage_options,
        )

    @property
    def chunks(self):
        static_coords = self.static_coords
        chunks = {name: static_coords[name].shape[0] for name in static_coords.keys()}
        assert self.timestep in ["1H", "1D"]
        if self.timestep == "1H":
            time_chunks = 24
        elif self.timestep == "1D":
            time_chunks = 1
        else:
            raise RuntimeError(
                f"Don't know how to deal with timestep {timestep} for chunking"
            )

        chunks.update({"time": time_chunks})
        return chunks

    @staticmethod
    def _check_dims_coords(dims, static_coords, model):
        # two types of grid def, assume one based on presence of "grid_latitude" or not
        if "grid_latitude" in dims:
            expected_coords = ["grid_longitude", "grid_latitude"]
        else:
            expected_coords = ["projection_x_coordinate", "projection_y_coordinate"]

        expected_dims = ["time"] + expected_coords

        pair_dict = {
            "static_coords": (expected_coords, list(static_coords.keys())),
            "dims": (expected_dims, dims),
        }

        for var_type, pair in pair_dict.items():
            expected, passed_in = pair
            # check all of expected were passed in
            if not all(map(lambda var: var in passed_in, expected)):
                raise ValueError(f"Expected to find all of {expected} in {var_type}")

    @property
    def dynamic_coords(self):
        dynamic_coords_data = {
            "time": pd.date_range(
                start=self.start_datetime, end=self.end_datetime, freq=self.timestep
            )
        }
        return {
            name: xr.Variable(dims=(name,), data=data)
            for name, data in dynamic_coords_data.items()
        }

    def _zstore_loader(self, attrs):
        time = attrs["time"]
        diag = attrs["variable_name"]

        time = pd.to_datetime(np.datetime64(time, "ns"))

        url = self._get_blob_url(diagnostic=diag, time=time)

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
        DIM_COORD_VARS = [
            "time",
            "projection_y_coordinate",
            "projection_x_coordinate",
            "forecast_reference_time",
            "forecast_day",
            "grid_longitude",
            "grid_latitude",
            "forecast_period",
        ]

        # coords only in some datasets
        VERTICAL_COORD_VARS = ["height", "depth", "pressure"]

        # variables that are not in coords or dims (including 'bnds' in dims)
        # but in all datasets
        NON_COORD_DIM_VARS = [
            "lambert_azimuthal_equal_area",
            "projection_y_coordinate_bnds",
            "projection_x_coordinate_bnds",
            "transverse_mercator",
            "experiment_number",
            "rotated_latitude_longitude",
        ]

        # vars that are not coords/dims but are optional
        TIME_BOUND_VARS = [
            "time_bnds",
            "forecast_period_bnds",
            "forecast_reference_time_bnds",
        ]

        # also has 'depth_bnds' optionally..
        # need to figure out which variable is the data variable
        NON_DATA_VARS = (
            DIM_COORD_VARS
            + VERTICAL_COORD_VARS
            + NON_COORD_DIM_VARS
            + TIME_BOUND_VARS
            + ["depth_bnds"]
        )

        data_var = list(set(dataset.variables) - set(NON_DATA_VARS))
        if len(data_var) > 1:
            raise RuntimeError("Expected to find only 1 data variable")
        data_var = data_var[0]
        return dataset[data_var]


class TimeSeriesDataset(SingleTimeDataset):
    def _get_blob_url(self, diagnostic, time=None):
        """Return the URL of a forecast file."""

        # convert all to strings
        if self.timestep == "1H":
            frequency = "hourly"
        elif self.timestep == "1D":
            frequency = "daily"
        else:
            raise RuntimeError(
                f"Don't know how to deal with timestep {timestep} for chunking"
            )

        time_str = datetime_to_iso_str(time).split("T")[0]
        obj_path = f"metoffice_{self.model}_{frequency}/{diagnostic}/{self.model}_{frequency}_{diagnostic}_{time_str}.nc"
        obj_path = f"{self.url_prefix}/{obj_path}"
        return f"{self.data_protocol}://{obj_path}"


class AQDataset(SingleTimeDataset):
    def _get_blob_url(self, diagnostic, time=None):
        """Return the URL of a forecast file."""

        # convert all to strings
        time_str = datetime_to_iso_str(time).split("T")[0]
        ag_str = f"_{self.aggregation}" if self.aggregation else ""
        obj_path = f"metoffice_{self.model}/{diagnostic}/{self.model}_{diagnostic}{ag_str}_{time_str}.nc"
        obj_path = f"{self.url_prefix}/{obj_path}"
        return f"{self.data_protocol}://{obj_path}"
