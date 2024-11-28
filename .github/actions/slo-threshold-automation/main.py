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
import boto3


def list_cloudwatch_log_groups():
    client = boto3.client('logs', region_name='ap-southeast-1')
    response = client.describe_log_groups()
    log_groups = response.get('logGroups', [])
    print(log_groups)
    return [log_group['logGroupName'] for log_group in log_groups]
    
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
    list_cloudwatch_log_groups()
