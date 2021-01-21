import logging
from io import BytesIO

import fsspec
import numpy as np
import pandas as pd
import xarray as xr
from ..zarrhypothetic.zarrhypothetic import HypotheticZarrStore
from .utils import (
    calc_cycle_validity_lead_times,
    datetime_to_iso_str,
    timedelta_to_duration_str,
    remove_trailing_z,
)

logger = logging.getLogger(__name__)


# TODO: remove hardcoded assumptions about MOGREPS-UK
class MODataset:
    def __init__(
        self,
        start_cycle,
        end_cycle,
        model,
        dims,
        diagnostics,
        static_coords,
        cycle_freq="1H",
        start_lead_time="0H",
        end_lead_time="126H",
        lead_time_freq="1H",
        **storage_options,
    ):
        """
        storage_options must contain the keys data_protocol and url_prefix

        NB: If using abfs, storage_options should contain the keys
        'account_name' and 'credential'
        """

        self._check_dims_coords(dims, static_coords, model)

        self.start_cycle = start_cycle
        self.end_cycle = end_cycle
        self.model = model
        self.dims = dims
        self.diagnostics = diagnostics
        self._static_coords = static_coords
        self.cycle_freq = cycle_freq
        self.start_lead_time = start_lead_time
        self.end_lead_time = end_lead_time
        self.lead_time_freq = lead_time_freq

        self.data_protocol = storage_options.pop("data_protocol")
        self.url_prefix = storage_options.pop("url_prefix")
        self.storage_options = storage_options
        self._validate_storage_options()

        # remove the 'Z' from the start/end points or xarray struggles...
        self.start_cycle = remove_trailing_z(self.start_cycle)
        self.end_cycle = remove_trailing_z(self.end_cycle)

        self._zstore = self._create_zstore()
        self._ds = None

    @staticmethod
    def _check_dims_coords(dims, static_coords, model):

        if "projection_x_coordinate" in static_coords:
            expected_coords = [
                "projection_x_coordinate",
                "projection_y_coordinate",
            ]
        else:
            expected_coords = [
                "longitude",
                "latitude",
            ]
        if model == "mo-atmospheric-mogreps-uk":
            expected_coords += ["realization"]

        expected_dims = [
            "forecast_reference_time",
            "forecast_period",
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

    def _validate_storage_options(self):
        ABFS_KEYS = ("account_name", "credential")
        if "abfs" not in self.data_protocol:
            return

        try:
            options = (
                self.storage_options["abfs"]
                if "::" in self.data_protocol
                else self.storage_options
            )
        except KeyError as err:
            msg = (
                "Expected to find 'abfs' key in storage_options for nested filesystems. "
                f"The associated value should be a dict containing the keys: {ABFS_KEYS}"
            )
            raise KeyError(msg) from err

        # need to check abfs keys are there:
        missing_keys = map(lambda k: k not in options, ABFS_KEYS)
        if any(missing_keys):
            msg = f"When using 'abfs', storage_options should contain the keys: {ABFS_KEYS}"
            raise KeyError(msg)

    @property
    def static_coords(self):
        static_coords = {}
        for name, defn in self._static_coords.items():
            data = defn["data"]
            if isinstance(data, dict):
                data = np.linspace(**data)
            else:
                data = np.array(data)
            static_coords[name] = xr.Variable(
                dims=(name,), data=data, attrs=defn.get("attrs")
            )
        return static_coords

    @property
    def coord_vars(self):
        return dict(self.static_coords, **self.dynamic_coords)

    @property
    def dynamic_coords(self):
        dynamic_coords_data = {
            "forecast_reference_time": pd.date_range(
                start=self.start_cycle, end=self.end_cycle, freq=self.cycle_freq
            ),
            "forecast_period": pd.timedelta_range(
                start=self.start_lead_time,
                end=self.end_lead_time,
                freq=self.lead_time_freq,
            ),
        }
        return {
            name: xr.Variable(dims=(name,), data=data)
            for name, data in dynamic_coords_data.items()
        }

    @property
    def chunks(self):
        static_coords = self.static_coords
        return {name: static_coords[name].shape[0] for name in static_coords.keys()}

    def _extract_data_as_dataarray(self, dataset):

        REQUIRED_COORD_VARS = []

        if "projection_x_coordinate" in self.static_coords:
            x_name, y_name = ["projection_x_coordinate", "projection_y_coordinate"]
        else:
            x_name, y_name = ["longitude", "latitude"]
            REQUIRED_COORD_VARS += ["latitude_longitude"]

        # coords in all datasets
        REQUIRED_COORD_VARS += [
            "time",
            "forecast_reference_time",
            "realization",
            y_name,
            "forecast_period",
            x_name,
        ]

        # coords only in some datasets
        VERTICAL_COORD_VARS = ["height", "depth", "pressure"]

        # variables that are not in coords or dims (including 'bnds' in dims)
        # but in all datasets
        REQUIRED_NON_COORD_DIM_VARS = [
            "lambert_azimuthal_equal_area",
            f"{x_name}_bnds",
            f"{y_name}_bnds",
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
            raise RuntimeError(
                f"Expected to find only 1 data variable but got: {data_var}"
            )
        data_var = data_var[0]
        return dataset[data_var]

    def _get_url(self, diagnostic, cycle_time=None, validity_time=None, lead_time=None):
        """Return the URL of a forecast file."""

        # determine all times
        cycle_time, validity_time, lead_time = calc_cycle_validity_lead_times(
            cycle_time, validity_time, lead_time
        )

        # convert all to strings
        cycle_time = datetime_to_iso_str(cycle_time)
        validity_time = datetime_to_iso_str(validity_time)
        lead_time = timedelta_to_duration_str(lead_time)

        obj_path = (
            f"{self.model}/{cycle_time}/{validity_time}-{lead_time}-{diagnostic}.nc"
        )
        obj_path = f"{self.url_prefix}/{obj_path}"
        return f"{self.data_protocol}://{obj_path}"

    def _read_from_url(self, url, mode="rb"):
        logger.info(f"Request: {url}")
        with fsspec.open(url, mode, **self.storage_options) as of:
            data = of.read()
        return data

    def _zstore_loader(self, attrs):
        ref_time = attrs["forecast_reference_time"]
        fcst_period = attrs["forecast_period"]
        diag = attrs["variable_name"]

        ref_time = pd.to_datetime(np.datetime64(ref_time, "ns"))
        fcst_period = pd.to_timedelta(np.timedelta64(fcst_period, "ns"))

        url = self._get_url(diagnostic=diag, cycle_time=ref_time, lead_time=fcst_period)

        try:
            data = self._read_from_url(url)
            data = xr.open_dataset(BytesIO(data))
            data = self._extract_data_as_dataarray(data)
            return data.values
        except FileNotFoundError:
            logger.info(f"NOT FOUND: {url}")
            return None

    def _create_zstore(self):
        return HypotheticZarrStore(
            dims=self.dims,
            coord_vars=self.coord_vars,
            data_vars=self.diagnostics,
            chunks=self.chunks,
            loader_function=self._zstore_loader,
            attrs=None,
            dtypes=None,
        )

    @property
    def ds(self):
        if self._ds is None:
            self._ds = xr.open_zarr(self._zstore, consolidated=True)
        return self._ds

    def to_xarray(self):
        return self.ds
