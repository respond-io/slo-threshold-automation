from utils.functions import (
    get_metrics_with_prefix,
    calculate_average_extended_statistic,
    update_metric_thresholds,
    process_and_save_yaml,
    process_slo_latency,
    yaml_to_json
)
from utils.cli import setup_cli
import json


def main():
    # Get the argument parser from cli.py and parse arguments
    parser = setup_cli()
    args = parser.parse_args()

    # Load configuration
    config_path = args.config
    
    config = json.loads(yaml_to_json(config_path))  
    # Process each workflow
    for workflow in config['slo']:
        process_slo_latency(workflow)

    print("SLO latency processing complete.")

if __name__ == "__main__":
    main()
