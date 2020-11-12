from .dataset import MODataset
import xarray as xr
import numpy as np
import pandas as pd
from .utils import datetime_to_iso_str
from io import BytesIO
import datetime
from met_office_datasets import __version__
from met_office_datasets.datasources import MetOfficeDataSource


class MetOfficeAQDataSource(MetOfficeDataSource):
    name = "met_office_aq"
    version = __version__

    def __init__(self,
                 start_cycle,
                 end_cycle,
                 cycle_frequency,
                 model,
                 dimensions,
                 diagnostics,
                 static_coords,
                 storage_options,
                 aggregation=None,
                 metadata=None
                 ):

        if end_cycle.lower() == 'latest':
            end_cycle = datetime_to_iso_str((datetime.datetime.now() - datetime.timedelta(hours=48)))

        self.aggregation = aggregation

        super().__init__(
            start_cycle=start_cycle,
            end_cycle=end_cycle,
            cycle_frequency=cycle_frequency,
            forecast_extent=None,
            model=model,
            dimensions=dimensions,
            static_coords=static_coords,
            diagnostics=diagnostics,
            storage_options=storage_options,
            metadata=metadata
        )

    def _open_dataset(self):
        self._ds = AQDataset(
            start_cycle=self.start_cycle,
            end_cycle=self.end_cycle,
            model=self.model,
            dims=self.dimensions,
            diagnostics=self.diagnostics,
            static_coords=self.static_coords,
            cycle_frequency=self.cycle_frequency,
            storage_options=self.storage_options,
            aggregation=self.aggregation
        ).ds


class AQDataset(MODataset):

    def __init__(
        self,
        start_cycle,
        end_cycle,
        model,
        dims,
        diagnostics,
        static_coords,
        cycle_frequency,
        storage_options,
        aggregation=None
    ):

        super().__init__(
            start_cycle=start_cycle,
            end_cycle=end_cycle,
            model=model,
            dims=dims,
            diagnostics=diagnostics,
            static_coords=static_coords,
            cycle_freq=cycle_frequency,
            start_lead_time=None,
            end_lead_time=None,
            lead_time_freq=None,
            **storage_options)

        self.aggregation = aggregation

    @ property
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

    @staticmethod
    def _check_dims_coords(dims, static_coords, model):
        expected_coords = [
            "projection_x_coordinate",
            "projection_y_coordinate",
        ]

        expected_dims = [
            "time"
        ] + expected_coords

        pair_dict = {
            "static_coords": (expected_coords, list(static_coords.keys())),
            "dims": (expected_dims, dims),
        }

        for var_type, pair in pair_dict.items():
            expected, passed_in = pair
            # check all of expected were passed in
            if not all(map(lambda var: var in passed_in, expected)):
                raise ValueError(f"Expected to find all of {expected} in {var_type}")

    @ property
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

    def _get_blob_url(
        self, diagnostic, time=None
    ):
        """Return the URL of a forecast file."""

        # convert all to strings
        time_str = datetime_to_iso_str(time).split('T')[0]
        ag_str = f"_{self.aggregation}" if self.aggregation else ""
        obj_path = (
            f"metoffice_{self.model}/{diagnostic}/{self.model}_{diagnostic}{ag_str}_{time_str}.nc"
        )
        obj_path = f"{self.url_prefix}/{obj_path}"
        return f"{self.data_protocol}://{obj_path}"

    def _zstore_loader(self, attrs):
        time = attrs["time"]
        diag = attrs["variable_name"]

        time = pd.to_datetime(np.datetime64(time, "ns"))

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

    @ staticmethod
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
