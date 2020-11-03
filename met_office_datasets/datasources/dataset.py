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
)


# TODO: remove hardcoded assumptions about MOGREPS-UK
class MODataset:
    def __init__(
        self,
        start_cycle,
        end_cycle,
        model,
        diagnostics,
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

        self.start_cycle = start_cycle
        self.end_cycle = end_cycle
        self.model = model
        self.diagnostics = diagnostics
        self.cycle_freq = cycle_freq
        self.start_lead_time = start_lead_time
        self.end_lead_time = end_lead_time
        self.lead_time_freq = lead_time_freq

        self.data_protocol = storage_options.pop("data_protocol")
        self.url_prefix = storage_options.pop("url_prefix")
        self.storage_options = storage_options
        self._validate_storage_options()

        # remove the 'Z' from the start/end points or xarray struggles...
        remove_trailing_z = (
            lambda dt_str: dt_str[:-1] if dt_str.endswith("Z") else dt_str
        )
        self.start_cycle = remove_trailing_z(self.start_cycle)
        self.end_cycle = remove_trailing_z(self.end_cycle)

        self._zstore = self._create_zstore()
        self._ds = None

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
    def dims(self):
        return (
            "forecast_reference_time",
            "forecast_period",
            "realization",
            "projection_y_coordinate",
            "projection_x_coordinate",
        )

    @staticmethod
    def _create_grid_coords():
        GRID_DEFINITION = {"x": (-1158000, 924000, 1042), "y": (-1036000, 902000, 970)}

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

    @property
    def static_coords(self):
        static_coords = self._create_grid_coords()
        NUM_REALIZATIONS = 3
        static_coords["realization"] = xr.Variable(
            dims=("realization",), data=np.arange(NUM_REALIZATIONS)
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

    @staticmethod
    def _extract_data_as_dataarray(dataset):
        # coords in all datasets
        REQUIRED_COORD_VARS = [
            "time",
            "forecast_reference_time",
            "realization",
            "projection_y_coordinate",
            "forecast_period",
            "projection_x_coordinate",
        ]

        # coords only in some datasets
        VERTICAL_COORD_VARS = ["height", "depth", "pressure"]

        # variables that are not in coords or dims (including 'bnds' in dims)
        # but in all datasets
        REQUIRED_NON_COORD_DIM_VARS = [
            "lambert_azimuthal_equal_area",
            "projection_y_coordinate_bnds",
            "projection_x_coordinate_bnds",
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

    def _get_fcst_url(
        self, diagnostic, cycle_time=None, validity_time=None, lead_time=None
    ):
        """Return the URL of a forecast file."""
        # model and diagnostic are strings
        # validity_time (datetime.datetime)
        # lead_time (datetime.timedelta)

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
        with fsspec.open(url, mode, **self.storage_options) as of:
            data = of.read()
        return data

    def _zstore_loader(self, attrs):
        ref_time = attrs["forecast_reference_time"]
        fcst_period = attrs["forecast_period"]
        diag = attrs["variable_name"]

        ref_time = pd.to_datetime(np.datetime64(ref_time, "ns"))
        fcst_period = pd.to_timedelta(np.timedelta64(fcst_period, "ns"))

        url = self._get_fcst_url(
            diagnostic=diag, cycle_time=ref_time, lead_time=fcst_period
        )

        try:
            data = self._read_from_url(url)
            data = xr.open_dataset(BytesIO(data))
            data = self._extract_data_as_dataarray(data)
            return data.values
        except FileNotFoundError:
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

    # passthrough magic methods to xarray dataset...
    def __copy__(self):
        return self.ds.__copy__()

    def __deepcopy__(self, memo=None):
        return self.ds.__deepcopy__(memo=memo)

    def __contains__(self, key):
        return key in self.ds

    def __len__(self):
        return len(self.ds)

    def __bool__(self):
        return bool(self.ds)

    def __iter__(self):
        return iter(self.ds)

    def __getitem__(self, key):
        return self.ds[key]

    def __setitem__(self, key, value):
        self.ds[key] = value

    def __delitem__(self, key):
        del self.ds[key]

    def __repr__(self):
        return repr(self.ds)

    def _repr_html_(self):
        return self.ds._repr_html_()
