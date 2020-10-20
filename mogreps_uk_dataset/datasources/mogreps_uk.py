
from mogreps_uk_dataset.zarrhypothetic.data import FCST_START_CYCLE, FCST_KNOWN_DIAGNOSTICS, FCST_KNOWN_MODELS, load_fcst_dataset
import datetime
import dateutil
import xarray as xr
import pandas as pd
import numpy as np
from mogreps_uk_dataset.zarrhypothetic.zarrhypothetic import HypotheticZarrStore
import sys
import os
import intake
import numpy
from mogreps_uk_dataset import __version__


class MogrepsUkDataSource(intake.source.base.DataSource):
    name = "mogreps_uk"
    version = __version__
    container = "ndarray"
    partition_access = True

    def __init__(self, metadata=None):
        super().__init__(
            metadata=metadata
        )

    def _get_schema(self):
        return intake.source.base.Schema(
            datashape=None,
            dtype="float64",
            shape=None,
            npartitions=1
        )

    def _get_partition(self, i):
        # Return the appropriate container of data here
        return self.read()

    def read(self):
        self._load_metadata()
        return xr.Dataset()  # Something that does something to go here!
        # return _load_mogreps_uk_dataset()

    def _close(self):
        # close any files, sockets, etc
        pass


# try:
#     import creds
# except ModuleNotFoundError:
#     print('Credentials file not found')

def _load_mogreps_uk_dataset():

    # ROOT_DIR = os.path.abspath(os.path.join(os.path.abspath(''), '..'))
    # sys.path.insert(0, ROOT_DIR)

    model = "mo-atmospheric-mogreps-uk"
    diagnostic = 'temperature_at_screen_level'
    cycle_time = dateutil.parser.isoparse(FCST_START_CYCLE)
    lead_time = datetime.timedelta(hours=12)

    datasets = {}
    for diag in FCST_KNOWN_DIAGNOSTICS:
        datasets[diag] = load_fcst_dataset(model=model,
                                           diagnostic=diag,
                                           cycle_time=cycle_time,
                                           lead_time=lead_time)

    # coords in all datasets
    REQUIRED_COORD_VARS = ['time',
                           'forecast_reference_time',
                           'realization',
                           'projection_y_coordinate',
                           'forecast_period',
                           'projection_x_coordinate']

    # coords only in some datasets
    VERTICAL_COORD_VARS = ['height', 'depth', 'pressure']

    # variables that are not in coords or dims (including 'bnds' in dims)
    # but in all datasets
    REQUIRED_NON_COORD_DIM_VARS = ['lambert_azimuthal_equal_area',
                                   'projection_y_coordinate_bnds',
                                   'projection_x_coordinate_bnds']

    # vars that are not coords/dims but are optional
    TIME_BOUND_VARS = ['time_bnds', 'forecast_period_bnds']

    # also has 'depth_bnds' optionally..

    # single level dims
    SINGLE_LEVEL_DIMS = ['bnds',
                         'realization',
                         'projection_y_coordinate',
                         'projection_x_coordinate']

    # need to figure out which variable is the data variable
    NON_DATA_VARS = (REQUIRED_COORD_VARS +
                     VERTICAL_COORD_VARS +
                     REQUIRED_NON_COORD_DIM_VARS +
                     TIME_BOUND_VARS +
                     ['depth_bnds'])

    def extract_data_as_dataarray(dataset):
        data_var = list(set(dataset.variables) - set(NON_DATA_VARS))
        if len(data_var) > 1:
            raise RuntimeError('Expected to find only 1 data variable')
        data_var = data_var[0]
        return dataset[data_var]

    def has_time_bounds(dataset):
        return set(TIME_BOUND_VARS).issubset(set(dataset.variables))

    def has_vertical_coord(dataset):
        return not set(VERTICAL_COORD_VARS).isdisjoint(set(dataset.coords))

    def has_vertical_dim(dataset):
        return not set(VERTICAL_COORD_VARS).isdisjoint(set(dataset.dims))

    multi_level_bounded = []
    multi_level = []
    single_level_bounded = []
    single_level = []
    for diag in FCST_KNOWN_DIAGNOSTICS:
        ds = datasets[diag]
        if has_vertical_dim(ds) and has_time_bounds(ds):
            lst = multi_level_bounded
        elif has_vertical_dim(ds):
            lst = multi_level
        elif has_time_bounds(ds):
            lst = single_level_bounded
        else:
            lst = single_level
        lst.append(diag)

    #############
    # ZarrHypothetic dataset
    ###########

    def create_dataset_vars(dataset, copy_vars, new_var_data):
        """
        Create new dataset variables by copying existing ones,
        optionally replacing the data.
        """
        ds_vars = {}
        for var in copy_vars:
            try:
                data = new_var_data[var]
                dims = (var,)
            except KeyError:
                data = dataset[var].data.copy()
                dims = dataset[var].dims

            ds_vars[var] = xr.Variable(
                dims=dims,
                data=data,
                attrs=dataset[var].attrs
            )
        return ds_vars

    # remove the 'Z' from the start/end points or xarray struggles...
    start_cycle = FCST_START_CYCLE[:-1]
    # TODO make 2
    end_cycle = (datetime.datetime.utcnow() - datetime.timedelta(hours=12)).replace(hour=0, minute=0, microsecond=0).strftime("%Y%m%dT%H%M")  # '20200924T0000' =

    max_lead_time = '126H'
    num_realizations = 3

    dims = ('forecast_reference_time', 'forecast_period',
            'realization', 'projection_y_coordinate', 'projection_x_coordinate')

    chunks = {
        'realization': num_realizations,
        'projection_y_coordinate': 970,
        'projection_x_coordinate': 1042,
    }

    new_var_data = {
        'realization': np.arange(num_realizations),
        'forecast_reference_time': pd.date_range(start=start_cycle, end=end_cycle, freq='1H'),
        'forecast_period': pd.timedelta_range(start='0H', end=max_lead_time, freq='1H'),
    }

    data_vars = single_level + single_level_bounded

    coord_vars = create_dataset_vars(ds, dims, new_var_data)

    def loader(attrs):
        ref_time = attrs['forecast_reference_time']
        fcst_period = attrs['forecast_period']
        diag = attrs['variable_name']

        ref_time = pd.to_datetime(np.datetime64(ref_time, 'ns'))
        fcst_period = pd.to_timedelta(np.timedelta64(fcst_period, 'ns'))

        try:
            data = load_fcst_dataset(model='mo-atmospheric-mogreps-uk',
                                     diagnostic=diag,
                                     cycle_time=ref_time,
                                     lead_time=fcst_period)
            data = extract_data_as_dataarray(data)
            return data.values
        except FileNotFoundError:
            return None

    zstore = HypotheticZarrStore(
        dims=dims,
        coord_vars=coord_vars,
        data_vars=data_vars,
        chunks=chunks,
        loader_function=loader,
        attrs=None,
        dtypes=None
    )

    ds = xr.open_zarr(zstore, consolidated=True)

    return ds
