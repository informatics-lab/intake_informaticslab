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


def remove_trailing_z(dt_str):
    return dt_str[:-1] if dt_str.endswith("Z") else dt_str
