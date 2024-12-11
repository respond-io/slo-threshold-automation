import yaml
from collections import OrderedDict
from datetime import datetime, timedelta
from cfn_flip import to_json, to_yaml
import boto3
import re
import os
from cfn_flip import to_json, to_yaml

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_session= os.getenv('AWS_SESSION_TOKEN')
aws_region = os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-1') 
print(aws_access_key_id)
print(aws_secret_access_key)
print(aws_session)

cloudwatch = boto3.client(
    'cloudwatch',
    region_name=aws_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    aws_session_token=aws_session
    
)


def yaml_to_json(yaml_path):
    """
    Converts a CloudFormation YAML file to JSON.
    
    Args:
        yaml_path (str): Path to the input YAML file.
    
    Returns:
        str: JSON content as a string.
    """
    try:
        with open(yaml_path, 'r') as file:
            yaml_content = file.read()
        json_content = to_json(yaml_content)
        return json_content
    except Exception as e:
        print(f"Error converting YAML to JSON: {e}")
        return None

def json_to_yaml(json_content, output_yaml_path):
    """
    Converts a JSON string to CloudFormation YAML format and saves it to a file.
    
    Args:
        json_content (str): JSON content as a string.
        output_yaml_path (str): Path to save the YAML file.
    """
    try:
        yaml_content = to_yaml(json_content)        
        with open(output_yaml_path, 'w') as file:
            file.write(yaml_content)
        print(f"Transformed YAML saved to {output_yaml_path}")
    except Exception as e:
        print(f"Error converting JSON to YAML: {e}")


def get_metrics_with_prefix(namespace, prefix):
    """
    Fetch all metrics with a specific prefix from a given namespace.
    """
    metrics = cloudwatch.list_metrics(Namespace=namespace)['Metrics']
    return [
        metric['MetricName']
        for metric in metrics
        if metric['MetricName'].endswith(prefix)
    ]

def calculate_average_extended_statistic(namespace, metric_name, dimension_name, dimension_value, extended_statistic, period, days):
    """
    Calculate the average value of a given extended statistic for a CloudWatch metric.
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    response = cloudwatch.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=[
            {'Name': dimension_name, 'Value': dimension_value}
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=period,
        ExtendedStatistics=[extended_statistic]
    )

    datapoints = response.get('Datapoints', [])
    if not datapoints:
        print(f"No data points found for {metric_name} in the last {days} days.")
        return None

    total_stat = sum(dp['ExtendedStatistics'][extended_statistic] for dp in datapoints)
    int(total_stat)
    return int(total_stat / len(datapoints))

def update_metric_thresholds(python_dict, average_stat_dict):
    """
    Updates the MetricThreshold in the given CloudFormation dictionary based on the average_stat_dict.
    """
    for resource_name, resource_data in python_dict.get("Resources", {}).items():
        try:
            metric_name = resource_data["Properties"]["Sli"]["SliMetric"]["MetricDataQueries"][0]["MetricStat"]["Metric"]["MetricName"]
            if metric_name in average_stat_dict:
                resource_data["Properties"]["Sli"]["MetricThreshold"] = average_stat_dict[metric_name]
                print(f"Updated MetricThreshold for {metric_name} to {average_stat_dict[metric_name]}")
            else:
                print(f"No matching entry in average_stat_dict for {metric_name}")
        except KeyError:
            print(f"Resource: {resource_name} does not have a valid MetricName or MetricThreshold property.")
    return python_dict

import json

def process_and_save_yaml(input_path, output_path, average_stat_dict):
    """
    Processes a CloudFormation YAML file: updates thresholds, cleans intrinsic prefixes, and saves the result.
    """
    json_content = yaml_to_json(input_path)  
    if json_content is None:
        print("Error in converting YAML to JSON.")
        return

    python_dict = json.loads(json_content)  
    updated_dict = update_metric_thresholds(python_dict, average_stat_dict)  
    updated_json_content = json.dumps(updated_dict)  

    json_to_yaml(updated_json_content, output_path)  

def process_slo_latency(workflow):
    """
    Process a single workflow configuration.

    Args:
        workflow (dict): A dictionary containing the configuration for a workflow.

    Returns:
        None
    """
    namespace = workflow['namespace']
    prefix = workflow['prefix']
    dimension_name = workflow['dimension_name']
    extended_statistic = workflow['extended_statistic']
    period = workflow['period']
    days = workflow['days']
    input_yaml_path = workflow['input_yaml_path']
    output_yaml_path = workflow['output_yaml_path']

    print(f"Processing workflow: {workflow['name']}")

    # Fetch metrics and calculate averages
    metric_names = get_metrics_with_prefix(namespace, prefix)
    average_stat_dict = {}

    for metric_name in metric_names:
        try:
            dimension_value = metric_name.split(prefix)[0]
            average_stat = calculate_average_extended_statistic(
                namespace, metric_name, dimension_name, dimension_value, extended_statistic, period, days
            )
            average_stat_dict[metric_name] = average_stat
            print(f"Average {extended_statistic} value for '{metric_name}': {average_stat:.2f} ms")
        except Exception as e:
            print(f"Error processing metric '{metric_name}': {e}")  

    # Process and save the updated YAML file
    process_and_save_yaml(input_yaml_path, output_yaml_path, average_stat_dict)
    print(f"Updated YAML saved to {output_yaml_path}")
