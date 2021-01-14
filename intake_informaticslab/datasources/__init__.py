import datetime

from intake.catalog.local import YAMLFilesCatalog
from intake.source.base import Schema
from intake_xarray.base import DataSourceMixin

from intake_informaticslab import __version__

from .dataset import MODataset
from .utils import datetime_to_iso_str

DATA_DELAY = 24 + 6  # num hours from current time that data is available


class LicenseNotExceptedError(RuntimeError):
    def __init__(self, license) -> None:
        message = f"Please acknowledge your acceptance of the '{license}' with the keyword argument `license_accepted=True`.' "
        super().__init__(message)


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
        dimensions,
        diagnostics,
        static_coords,
        storage_options,
        license=None,
        metadata=None,
        **kwargs,
    ):
        super().__init__(metadata=metadata)

        self.license = license
        self.license_accepted = kwargs.get("license_accepted", False)

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
        self.dimensions = dimensions
        self.diagnostics = diagnostics
        self.static_coords = static_coords
        self.storage_options = storage_options
        self._ds = None

    def _open_dataset(self):
        if self.license:
            license_accepted = self.license_accepted
            if not (str(license_accepted).upper() == "TRUE"):
                raise LicenseNotExceptedError(self.license)

        self._ds = MODataset(
            start_cycle=self.start_cycle,
            end_cycle=self.end_cycle,
            model=self.model,
            dims=self.dimensions,
            diagnostics=self.diagnostics,
            static_coords=self.static_coords,
            cycle_freq=self.cycle_frequency,
            start_lead_time="0H",
            end_lead_time=self.forecast_extent,
            lead_time_freq="1H",
            **self.storage_options,
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


class MergedMetOfficeDataSource(YAMLFilesCatalog):
    name = "merged_met_office"
    version = __version__

    def __init__(self, path, flatten=True, **kwargs):
        metadata = kwargs.pop("metadata")
        super().__init__(path, flatten=flatten, metadata=metadata)

        self._kwargs = kwargs
        self._ds = None

    def to_dask(self):
        if self._ds is not None:
            return self._ds

        for entry in self._entries.values():
            dataset = entry(**self._kwargs).to_dask()
            if self._ds is None:
                self._ds = dataset
            else:
                self._ds = self._ds.merge(dataset)
        return self._ds

    def read_chunked(self):
        return self.to_dask()
