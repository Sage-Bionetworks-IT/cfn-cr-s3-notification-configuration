import json
import boto3
from crhelper import CfnResource
from os import environ

logger = logging.getLogger(__name__)
helper = CfnResource(
    json_logging=False, log_level='DEBUG', boto_level='CRITICAL')

def _get_comma_delimited_list(event, parameter):
    value = event['ResourceProperties'].get(parameter)
    return [x.strip() for x in value.split(',')] if value else []

def get_parameters(event):
    notification_bucket = event['ResourceProperties']['NotificationBucket']
    lambda_function_arn = event['ResourceProperties']['LambdaFunctionArn']
    labda_notification_events = _get_comma_delimited_list(event, 'LambdaNotificationEvents')
    return notification_bucket, lambda_function_arn, labda_notification_events

try:
    s3 = boto3.client("s3")
except Exception as e:
    helper.init_failure(e)

def add_notification(notification_bucket, lambda_function_arn, labda_notification_events):
    bucket_notification = s3.BucketNotification(notification_bucket)
    response = bucket_notification.put(
        NotificationConfiguration={
            'LambdaFunctionConfigurations': [
                {
                    'LambdaFunctionArn': lambda_function_arn,
                    'Events': labda_notification_events
                }
            ]
        }
    )
    logger.info("added bucket notification to " + notification_bucket)
    return notification_bucket

def delete_notification(bucket):
    bucket_notification = s3.BucketNotification(bucket)
    response = bucket_notification.put(
        NotificationConfiguration={}
    )
    logger.info("removed bucket notification from " + bucket)


@helper.create
@helper.update
def create(event, context):
    logger.debug("Received event: " + json.dumps(event, sort_keys=False))
    return add_notification(*get_parameters(event))


@helper.delete
def delete(event, context):
    logger.debug("Received event: " + json.dumps(event, sort_keys=False))
    notification_bucket = event['ResourceProperties']['NotificationBucket']
    logger.info("remove bucket notification from " + notification_bucket)
    return delete_notification(notification_bucket)


def lambda_handler(event, context):
    helper(event, context)
