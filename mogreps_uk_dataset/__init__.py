

import os

# os.environ["BLOB_ACCOUNT_NAME"] = "improverdata"
# os.environ["FCST_BLOB_CONTAINER_NAME"] = "level1"
# os.environ["FCST_BLOB_CREDENTIAL"] =

os.environ["BLOB_ACCOUNT_NAME"] = "metdatasa"
os.environ["FCST_BLOB_CONTAINER_NAME"] = "met-office-models-ncdf"
__version__ = '0.0.1'


from .datasources.mogreps_uk import MogrepsUkDataSource # ensure this import is last and after __version__