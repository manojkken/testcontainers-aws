"""
testcontainers-aws: Simplified AWS service testing with Testcontainers

Provides easy-to-use abstractions for testing AWS services using Testcontainers
and LocalStack. Automatically handles container lifecycle, service initialization,
and boto3 client configuration.
"""

from testcontainers_aws.core import AWSTestEnvironment

__version__ = "0.2.0"
__all__ = ["AWSTestEnvironment"]
