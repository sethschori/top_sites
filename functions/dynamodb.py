"""
AWS DynamoDB functions
"""
import boto3
from botocore.exceptions import ClientError
from error_handling import handle_error


class Dynamo(object):
    """
    Class for AWS DynamoDB functions.
    """
    def __init__(self, profile_name='default'):
        """
        Initialize the Dynamo object using profile_name.
        :param profile_name: If you're using AWS for other purposes beyond 
        top_sites, then you likely already have a config and/or credentials 
        file. (See details here: https://docs.aws.amazon.com/cli/latest
        /userguide/cli-chap-getting-started.html) If you're using the 
        default profile to store 'region', 'aws_access_key_id', and
        'aws_secret_access_key' values, then you don't need to pass 
        profile_name when instantiating a Dynamo object.
        """
        self.profile_name = profile_name
        self.boto_sess = boto3.session.Session(
            profile_name=self.profile_name,
        )
        self.dynamodb = self.boto_sess.resource('dynamodb')

    def get_all_rows(self, table_name):
        """
        Retrieves all rows by scanning a DynamoDB table.
        :param table_name: the name of the table to scan
        :return: returns all rows as a list of dicts if successful, returns 
        None if unsuccessful
        """
        table = self.dynamodb.Table(table_name)

        try:
            response = table.scan()
        except ClientError as e:
            error = e.response['Error']['Code']
            if error == 'ResourceNotFoundException':
                handle_error(
                    exc=error,
                    err=e,
                    msg='table_name "{t}" was not found'.format(t=table_name)
                )
            else:
                handle_error(
                    exc=error,
                    err=e,
                    msg='unknown error'
                )
            return None

        items = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response['Items'])

        return items

    def batch_update_rows(self, table_name, items):
        """
        Takes a list of object(s) and updates those in DynamoDB table_name
        :param table_name: the name of the DynamoDB table to be updated
        :param items: a list of object(s)
        :return: True if succeeded, false if failed
        """
        table = self.dynamodb.Table(table_name)

        try:
            with table.batch_writer() as batch:
                for item in items:
                    item = vars(item)
                    batch.put_item(Item=item)
        except ClientError as e:
            handle_error(
                exc=ClientError,
                err=e,
                msg="unknown error"
            )
            return False

        return True
