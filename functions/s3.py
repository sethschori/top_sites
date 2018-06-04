"""
Functions to interact with AWS's S3 (Simple Storage Service).
"""
from boto3 import session, exceptions
from botocore.exceptions import ClientError
from error_handling import handle_error


class S3(object):
    """
    Class for AWS S3 functions.
    """
    def __init__(self, profile_name='top-sites', bucket='top-sites-output'):
        """
        Initialize the S3 object using profile_name.
        :param profile_name: If you're using AWS for other purposes beyond 
        top_sites, then you likely already have a config and/or credentials 
        file. (See details here: https://docs.aws.amazon.com/cli/latest
        /userguide/cli-chap-getting-started.html) If you're using the 
        default profile to store 'region', 'aws_access_key_id', and
        'aws_secret_access_key' values, then you don't need to pass 
        profile_name when instantiating a Dynamo object.
        :param bucket: The S3 bucket which will be acted on.
        """
        self.profile_name = profile_name
        self.boto_sess = session.Session(
            profile_name=self.profile_name,
        )
        self.s3 = self.boto_sess.resource('s3')
        self.bucket = self.s3.Bucket(bucket)

    def upload_file(self, file, public_read=False):
        """
        Upload a file to an S3 bucket and optional folder.
        :param file: The file to be uploaded.
        :return: True if succeeded, False if failed
        """
        try:
            if public_read:
                self.bucket.upload_file(
                    Filename='../output/index.html',
                    Key='index.html',
                    ExtraArgs={'ACL': 'public-read'}
                )
            else:
                self.bucket.upload_file(
                    Filename='../output/index.html',
                    Key='index.html'
                )
        except exceptions.S3UploadFailedError as e:
            handle_error(
                exc=exceptions.S3UploadFailedError,
                err=e
            )
            return False
        return True

    def upload_file_public_read(self, file):
        result = self.upload_file(file, public_read=True)
        if result:
            return True
        return False
