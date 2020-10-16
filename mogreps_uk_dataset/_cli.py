def validate(ARGS):
    """
    Validate command line arguments

    Parameters
    ----------
    ARGS : Namespace
        Command line arguments
    """
    return *ARGS


def main():
    """
    Command line interface for package, if desired.
    If not, remove the `entry_points...` line from `setup.py`
    """
    PARSER = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # parse arguments from command line
    ARGS = PARSER.parse_args()
    # validate command line arguments
    # import packages after parsing to speed up command line responsiveness
    validated_args = validate(ARGS)
    # run genome-interval-similarity function
    import run
    run(**validated_args)