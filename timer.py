import boto3
import json
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


sts = boto3.client('sts')

a = "arn:aws:states:eu-west-1:304191265855:execution:MyStateMachine:i-abcd1111"
sfn = boto3.client('stepfunctions')


def retrieve_account_id():
    response = sts.get_caller_identity()
    account_id = response['Account']
    return account_id

def retrieve_delete_time():
    period = int(os.environ['RetentionPeriod'])
    delete_time = datetime.now() + timedelta(hours=period)
    delete_time = format(delete_time, '%Y-%m-%dT%H:%M:%SZ')
    return delete_time

def start_clean_up(account_id, input_data, instance_id):   
    response = sfn.start_execution(
        stateMachineArn='arn:aws:states:eu-west-1:{}:stateMachine:{}'.format(account_id,os.environ['CleanUpSfnName']),
        name=instance_id,
        input=input_data
    )
    execution_arn = response['executionArn']
    return execution_arn

def stop_cleanup_execution(account_id,instance_id):
    response = sfn.stop_execution(
        executionArn='arn:aws:states:eu-west-1:{}:execution:{}:{}'.format(account_id,os.environ['CleanUpSfnName'],instance_id),
        error='0',
        cause='instance terminated'
    )
    return response

def lambda_handler(event, handler):
    print(event)
    print(type(event))
    account_id = retrieve_account_id()
    instance_id = event['detail']['instance-id']
    if event['detail']['state'] == 'running':
    #event = event['event']
        delete_time =  retrieve_delete_time()

        input={'DeletionTime': delete_time,
                'InstanceId': instance_id}
        
        input_data = json.dumps(input)
        start_clean_up(account_id, input_data, instance_id)

        return input
    elif event['detail']['state'] == 'terminated':
        try:
            stop_cleanup_execution(account_id, instance_id)
        except Exception as e:
            logger.error(str(e))
