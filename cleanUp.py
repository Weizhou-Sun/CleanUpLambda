import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2_client = boto3.client('ec2')
ec2 = boto3.resource('ec2')

def clean_up(instance_id):
    response = ec2_client.terminate_instances(
        InstanceIds=[
            instance_id,
        ]
    )
    waiter = ec2_client.get_waiter('instance_terminated')
    waiter.wait(
        InstanceIds=[
            instance_id,
        ]
    )

def instance_terminated(instance_id):
    response = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'instance-state-name',
                'Values': [
                    'shutting-down', 'terminated'
                ]
            }
        ],
        InstanceIds=[
            instance_id,
        ]
    )
    if len(response['Reservations']) != 0:
        return True
    else:
        return False

def instance_protected(instance_id):
    response = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'tag:{}'.format(os.environ['TerminationProtectionTagName']),
                'Values': [
                    'true', 'True', 'TRUE',
                ]
            }
        ],
        InstanceIds=[
            instance_id,
        ]
    )
    print(response)
    if len(response['Reservations']) != 0:
        return True
    else:
        return False

def lambda_handler(input, context):
    instance_id = input['InstanceId']

    if instance_terminated(instance_id):
        logger.info('Instance %s already terminated!' % instance_id)
    else:
        if instance_protected(instance_id):
            logger.info('Instance %s is protected with tag %s' %
                        (instance_id, os.environ['TerminationProtectionTagName']))
        else:
            try:
                clean_up(instance_id)
                logger.info('Instance %s is terminated'% instance_id)
            except Exception as e:
                logger.error(str(e))

