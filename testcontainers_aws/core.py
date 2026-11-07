"""Core AWS test environment orchestration."""

import os
from typing import Dict, List, Optional, Any
import boto3
from testcontainers.localstack import LocalStackContainer

from testcontainers_aws.services.s3 import S3ServiceManager
from testcontainers_aws.services.dynamodb import DynamoDBServiceManager
from testcontainers_aws.services.sqs import SQSServiceManager
from testcontainers_aws.services.kinesis import KinesisServiceManager
from testcontainers_aws.services.lambda_service import LambdaServiceManager
from testcontainers_aws.services.sns import SNSServiceManager


class AWSTestEnvironment:
    """
    Orchestrates AWS services for testing using LocalStack.

    Provides a unified interface to spin up and configure multiple AWS services
    in a single container, with automatic boto3 client configuration and
    helper methods for common testing operations.

    Example:
        ```python
        with AWSTestEnvironment(services=['s3', 'dynamodb']) as aws:
            s3 = aws.get_s3_client()
            dynamodb = aws.get_dynamodb_client()

            # Use clients for testing
            s3.create_bucket(Bucket='test-bucket')
        ```
    """

    # Map service names to LocalStack service strings
    SERVICE_MAP = {
        's3': 's3',
        'dynamodb': 'dynamodb',
        'sqs': 'sqs',
        'sns': 'sns',
        'kinesis': 'kinesis',
        'lambda': 'lambda',
        'logs': 'logs',
        'cloudformation': 'cloudformation',
        'iam': 'iam',
        'sts': 'sts',
        'ssm': 'ssm',
        'secretsmanager': 'secretsmanager',
    }

    def __init__(
        self,
        services: Optional[List[str]] = None,
        init_config: Optional[Dict[str, Any]] = None,
        image_tag: str = "4.14",
    ):
        """
        Initialize AWS test environment.

        Args:
            services: List of AWS services to enable (e.g., ['s3', 'dynamodb']).
                     If None, all common services are enabled.
            init_config: Configuration for initializing resources (buckets, tables, etc.)
            image_tag: LocalStack Docker image tag (default: '4.14', the last release
                that runs without a LocalStack auth token)
        """
        self.services = services or ['s3', 'dynamodb', 'sqs', 'kinesis']
        self.init_config = init_config or {}
        self.image_tag = image_tag

        self._container: Optional[LocalStackContainer] = None
        self._clients: Dict[str, Any] = {}
        self._service_managers: Dict[str, Any] = {}

    def __enter__(self) -> 'AWSTestEnvironment':
        """Start the container and initialize services."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the container and cleanup."""
        self.stop()

    def start(self) -> None:
        """Start LocalStack container and initialize configured services."""
        # Convert service names to LocalStack service strings
        localstack_services = [self.SERVICE_MAP.get(s, s) for s in self.services]

        # Create and start LocalStack container
        self._container = LocalStackContainer(
            image=f"localstack/localstack:{self.image_tag}"
        )

        # Set services to enable (with_services overwrites SERVICES, so pass them all at once)
        self._container = self._container.with_services(*localstack_services)

        # LocalStack runs Lambda functions in sibling containers via the host Docker socket
        if 'lambda' in self.services:
            self._container = self._container.with_volume_mapping(
                "/var/run/docker.sock", "/var/run/docker.sock", "rw"
            )

        # Pass auth token through when set (required for LocalStack 2026.03.0+ / latest)
        auth_token = os.environ.get("LOCALSTACK_AUTH_TOKEN")
        if auth_token:
            self._container = self._container.with_env("LOCALSTACK_AUTH_TOKEN", auth_token)

        self._container.start()

        # Initialize service managers
        self._init_service_managers()

        # Run initialization tasks
        self._initialize_resources()

    def stop(self) -> None:
        """Stop the LocalStack container."""
        if self._container:
            self._container.stop()
            self._container = None
            self._clients.clear()
            self._service_managers.clear()

    def _init_service_managers(self) -> None:
        """Initialize service manager instances."""
        if 's3' in self.services:
            self._service_managers['s3'] = S3ServiceManager(self)

        if 'dynamodb' in self.services:
            self._service_managers['dynamodb'] = DynamoDBServiceManager(self)

        if 'sqs' in self.services:
            self._service_managers['sqs'] = SQSServiceManager(self)

        if 'kinesis' in self.services:
            self._service_managers['kinesis'] = KinesisServiceManager(self)

        if 'lambda' in self.services:
            self._service_managers['lambda'] = LambdaServiceManager(self)

        if 'sns' in self.services:
            self._service_managers['sns'] = SNSServiceManager(self)

    def _initialize_resources(self) -> None:
        """Initialize AWS resources based on init_config."""
        # Initialize S3 buckets
        if 's3_buckets' in self.init_config and 's3' in self._service_managers:
            for bucket in self.init_config['s3_buckets']:
                if isinstance(bucket, str):
                    self._service_managers['s3'].create_bucket(bucket)
                elif isinstance(bucket, dict):
                    self._service_managers['s3'].create_bucket(**bucket)

        # Initialize DynamoDB tables
        if 'dynamodb_tables' in self.init_config and 'dynamodb' in self._service_managers:
            for table in self.init_config['dynamodb_tables']:
                self._service_managers['dynamodb'].create_table(**table)

        # Initialize SQS queues
        if 'sqs_queues' in self.init_config and 'sqs' in self._service_managers:
            for queue in self.init_config['sqs_queues']:
                if isinstance(queue, str):
                    self._service_managers['sqs'].create_queue(queue)
                elif isinstance(queue, dict):
                    self._service_managers['sqs'].create_queue(**queue)

        # Initialize Kinesis streams
        if 'kinesis_streams' in self.init_config and 'kinesis' in self._service_managers:
            for stream in self.init_config['kinesis_streams']:
                if isinstance(stream, str):
                    self._service_managers['kinesis'].create_stream(stream)
                elif isinstance(stream, dict):
                    self._service_managers['kinesis'].create_stream(**stream)

        # Initialize SNS topics
        if 'sns_topics' in self.init_config and 'sns' in self._service_managers:
            for topic in self.init_config['sns_topics']:
                if isinstance(topic, str):
                    self._service_managers['sns'].create_topic(topic)
                elif isinstance(topic, dict):
                    self._service_managers['sns'].create_topic(**topic)

        # Initialize Lambda functions
        if 'lambda_functions' in self.init_config and 'lambda' in self._service_managers:
            for function in self.init_config['lambda_functions']:
                self._service_managers['lambda'].create_function(**function)

    def get_client(self, service_name: str) -> Any:
        """
        Get a boto3 client for the specified AWS service.

        Args:
            service_name: AWS service name (e.g., 's3', 'dynamodb')

        Returns:
            Configured boto3 client for the service
        """
        if service_name not in self._clients:
            if not self._container:
                raise RuntimeError("Container not started. Use 'with' statement or call start().")

            endpoint_url = self._container.get_url()

            self._clients[service_name] = boto3.client(
                service_name,
                endpoint_url=endpoint_url,
                aws_access_key_id='test',
                aws_secret_access_key='test',
                region_name='us-east-1',
            )

        return self._clients[service_name]

    def get_s3_client(self):
        """Get pre-configured S3 client."""
        return self.get_client('s3')

    def get_dynamodb_client(self):
        """Get pre-configured DynamoDB client."""
        return self.get_client('dynamodb')

    def get_sqs_client(self):
        """Get pre-configured SQS client."""
        return self.get_client('sqs')

    def get_kinesis_client(self):
        """Get pre-configured Kinesis client."""
        return self.get_client('kinesis')

    def get_sns_client(self):
        """Get pre-configured SNS client."""
        return self.get_client('sns')

    def get_lambda_client(self):
        """Get pre-configured Lambda client."""
        return self.get_client('lambda')

    @property
    def s3(self):
        """Access S3 service manager with helper methods."""
        return self._service_managers.get('s3')

    @property
    def dynamodb(self):
        """Access DynamoDB service manager with helper methods."""
        return self._service_managers.get('dynamodb')

    @property
    def sqs(self):
        """Access SQS service manager with helper methods."""
        return self._service_managers.get('sqs')

    @property
    def kinesis(self):
        """Access Kinesis service manager with helper methods."""
        return self._service_managers.get('kinesis')

    @property
    def lambda_(self):
        """Access Lambda service manager with helper methods."""
        return self._service_managers.get('lambda')

    @property
    def sns(self):
        """Access SNS service manager with helper methods."""
        return self._service_managers.get('sns')

    @property
    def endpoint_url(self) -> str:
        """Get the LocalStack endpoint URL."""
        if not self._container:
            raise RuntimeError("Container not started")
        return self._container.get_url()
