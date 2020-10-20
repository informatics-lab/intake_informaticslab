import os
import time
from io import BytesIO

import fsspec
import xarray as xr

from mogreps_uk_dataset.conn import BLOB_ACCOUNT_NAME, BLOB_ACCOUNT_URL, FCST_BLOB_CONTAINER_NAME, FCST_BLOB_CREDENTIAL


# the data that are available in the blob container
FCST_KNOWN_MODELS = [
    "mo-atmospheric-mogreps-uk",
]

FCST_KNOWN_DIAGNOSTICS = [
    "cloud_amount_of_low_cloud",
    "cloud_amount_of_medium_cloud",
    "cloud_amount_of_total_cloud",
    "fog_fraction_at_screen_level",
    "hail_fall_accumulation-PT01H",
    "height_ASL_at_freezing_level",
    "lightning_flash_accumulation-PT01H",
    "radiation_flux_in_longwave_downward_at_surface",
    "radiation_flux_in_shortwave_diffuse_downward_at_surface",
    "radiation_flux_in_shortwave_direct_downward_at_surface",
    "radiation_flux_in_shortwave_total_downward_at_surface",
    "rainfall_accumulation-PT01H",
    "relative_humidity_at_screen_level",
    "sensible_heat_flux_at_surface",
    "snow_depth_water_equivalent",
    "snowfall_accumulation-PT01H",
    "soil_temperature_on_soil_levels",
    "temperature_at_screen_level",
    "temperature_at_screen_level_max-PT01H",
    "temperature_at_screen_level_min-PT01H",
    "temperature_at_surface",
    "temperature_on_height_levels",
    "visibility_at_screen_level",
    "wet_bulb_potential_temperature_on_pressure_levels",
    "wind_direction_at_10m",
    "wind_speed_at_10m",
    "wind_speed_at_10m_max-PT01H",
]

# FCST_START_CYCLE = "20200823T0000Z"
FCST_START_CYCLE = "20201018T0900Z"

CACHE_DIR = f'{os.environ["HOME"]}/cache'
CACHE_OPTIONS = {
    "cache_check": False,
    "check_files": False,
    "expiry_time": False,
    "same_names": True,
    "compression": None,
}


def timedelta_to_duration_str(td):
    """Convert a timedelta object into a duration string e.g: PT<hhhh>H<mm>M."""
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    hours += td.days * 24
    hours = int(hours)
    assert seconds == 0
    return f"PT{hours:04}H{minutes:02}M"


def datetime_to_iso_str(dt):
    """Convert a datetime object into an ISO string representation."""
    return dt.strftime("%Y%m%dT%H%MZ")


def calc_cycle_validity_lead_times(cycle_time=None, validity_time=None, lead_time=None):
    """Given two of cycle time, validity time and lead time, return all three."""
    num_inputs = sum(
        map(lambda x: 1 if x is not None else 0, [cycle_time, validity_time, lead_time])
    )
    if num_inputs != 2:
        raise RuntimeError("Expected 2 of cycle_time, validity_time and lead_time")
    if not validity_time:
        validity_time = cycle_time + lead_time
    elif not cycle_time:
        cycle_time = validity_time - lead_time
    elif not lead_time:
        lead_time = validity_time - cycle_time
    return cycle_time, validity_time, lead_time


def get_fcst_url(
    model, diagnostic, cycle_time=None, validity_time=None, lead_time=None
):
    """Return the URL of a forecast file."""
    # model and diagnostic are strings
    # validity_time (datetime.datetime)
    # lead_time (datetime.timedelta)

    assert model in FCST_KNOWN_MODELS
    assert diagnostic in FCST_KNOWN_DIAGNOSTICS

    # determine all times
    cycle_time, validity_time, lead_time = calc_cycle_validity_lead_times(
        cycle_time, validity_time, lead_time
    )

    # convert all to strings
    cycle_time = datetime_to_iso_str(cycle_time)
    validity_time = datetime_to_iso_str(validity_time)
    lead_time = timedelta_to_duration_str(lead_time)

    obj_path = f"{model}/{cycle_time}/{validity_time}-{lead_time}-{diagnostic}.nc"
    obj_path = f"{FCST_BLOB_CONTAINER_NAME}/{obj_path}"
    return f"abfs://{obj_path}"
    # if https:
    # return f"{BLOB_ACCOUNT_URL}/{obj_path}"


def load_from_url(
    url,
    mode="rb",
    account_name=BLOB_ACCOUNT_NAME,
    credential=FCST_BLOB_CREDENTIAL,
    cache=True,
    cache_dir=CACHE_DIR,
):

    storage_options = {"account_name": account_name, "credential": credential}

    if cache:
        protocol, _ = url.split("://", 1)
        url = f"filecache::{url}"
        storage_options = {
            protocol: storage_options,
            "filecache": dict(cache_storage=cache_dir, **CACHE_OPTIONS),
        }

    with fsspec.open(url, mode, **storage_options) as of:
        data = of.read()
    return data


def load_fcst_dataset(
    model, diagnostic, cycle_time=None, validity_time=None, lead_time=None
):
    url = get_fcst_url(
        model=model,
        diagnostic=diagnostic,
        cycle_time=cycle_time,
        validity_time=validity_time,
        lead_time=lead_time,
    )
    data = load_from_url(url)
    return xr.open_dataset(BytesIO(data))
