import datetime

from intake.source.base import Schema
from intake_xarray.base import DataSourceMixin
from met_office_datasets import __version__

from .dataset import MODataset
from .utils import datetime_to_iso_str

DATA_DELAY = 24  # num hours from current time that data is available


class MetOfficeDataSource(DataSourceMixin):
    name = "met_office"
    version = __version__

    def __init__(
        self,
        start_cycle,
        end_cycle,
        cycle_frequency,
        forecast_extent,
        model,
        diagnostics,
        storage_options,
        metadata=None,
    ):
        super().__init__(metadata=metadata)
        if end_cycle.lower() == "latest":
            end_cycle = datetime.datetime.utcnow() - datetime.timedelta(
                hours=DATA_DELAY
            )
            end_cycle = datetime_to_iso_str(end_cycle)

        self.start_cycle = start_cycle
        self.end_cycle = end_cycle
        self.cycle_frequency = cycle_frequency
        self.forecast_extent = forecast_extent
        self.model = model
        self.diagnostics = diagnostics
        self.storage_options = storage_options
        self._ds = None

    def _open_dataset(self):
        self._ds = MODataset(
            start_cycle=self.start_cycle,
            end_cycle=self.end_cycle,
            model=self.model,
            diagnostics=self.diagnostics,
            cycle_freq=self.cycle_frequency,
            start_lead_time="0H",
            end_lead_time=self.forecast_extent,
            lead_time_freq="1H",
            **self.storage_options
        ).ds

    def _get_schema(self):
        # adapted from intake-xarray driver
        if self._ds is None:
            self._open_dataset()

            # assume rectangular data (shared coords across all data vars)
            metadata = {
                "dims": dict(self._ds.dims),
                "data_vars": self.diagnostics,
                "coords": tuple(self._ds.coords.keys()),
            }
            metadata.update(self._ds.attrs)
            self._schema = Schema(
                datashape=None,
                dtype=None,
                shape=None,
                npartitions=None,
                extra_metadata=metadata,
            )
        return self._schema
