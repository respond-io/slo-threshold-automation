import argparse

def setup_cli():
    """
    Set up and return the argument parser for the CLI.
    """
    parser = argparse.ArgumentParser(description="Process SLO latency workflows.")

    # Add CLI arguments
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the configuration file (e.g., SLO.yaml)"
    )

    return parser
