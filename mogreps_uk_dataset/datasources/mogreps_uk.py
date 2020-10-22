import intake

from mogreps_uk_dataset import __version__
from mogreps_uk_dataset.conn import (BLOB_ACCOUNT_NAME, BLOB_CONTAINER_NAME,
                                     BLOB_CREDENTIAL)
from mogreps_uk_dataset.datasources.dataset import MODataset


class MogrepsUkDataSource(intake.source.base.DataSource):
    name = "mogreps_uk"
    version = __version__
    container = "ndarray"
    partition_access = True

    def __init__(self, metadata=None):
        super().__init__(metadata=metadata)

    def _get_schema(self):
        return intake.source.base.Schema(
            datashape=None, dtype="float64", shape=None, npartitions=1
        )

    def _get_partition(self, i):
        # Return the appropriate container of data here
        return self.read()

    def read(self):
        self._load_metadata()
        dataset = MODataset(
            start_cycle="20201018T0800Z",
            end_cycle="20201020T1200Z",
            account_name=BLOB_ACCOUNT_NAME,
            url_prefix=BLOB_CONTAINER_NAME,
            credential=BLOB_CREDENTIAL,
        )
        return dataset.ds

    def _close(self):
        # close any files, sockets, etc
        pass
