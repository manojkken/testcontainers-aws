# testcontainers-aws

**Simplified AWS service testing with Testcontainers** - Orchestrate LocalStack and AWS services for integration tests with minimal boilerplate.

[![CI](https://github.com/manojkken/testcontainers-aws/actions/workflows/ci.yml/badge.svg)](https://github.com/manojkken/testcontainers-aws/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/testcontainers-aws.svg)](https://badge.fury.io/py/testcontainers-aws)
[![Python Versions](https://img.shields.io/pypi/pyversions/testcontainers-aws.svg)](https://pypi.org/project/testcontainers-aws/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why testcontainers-aws?

Testing AWS services locally is tedious:
- Manual container setup for each service
- Repetitive boto3 client configuration
- Boilerplate code for resource initialization
- No pytest fixtures for common patterns

**testcontainers-aws** solves this:

```python
from testcontainers_aws import AWSTestEnvironment

# Before: Manual setup with testcontainers
with LocalStackContainer() as localstack:
    localstack.execInContainer("awslocal", "s3", "mb", "s3://bucket")
    client = boto3.client('s3', endpoint_url=localstack.get_url(), ...)
    # More configuration...

# After: One line with testcontainers-aws
with AWSTestEnvironment(services=['s3', 'dynamodb']) as aws:
    s3 = aws.get_s3_client()  # Pre-configured, ready to use
    aws.s3.create_bucket('test-bucket')  # Helper methods
```

## Features

- ✅ **Single container orchestration** - Spin up multiple AWS services in one LocalStack container
- ✅ **Auto-configured boto3 clients** - No manual endpoint/credential setup
- ✅ **Service helper methods** - Create buckets, tables, queues with simple method calls
- ✅ **Pytest fixtures** - Ready-to-use fixtures for common testing patterns
- ✅ **Resource auto-initialization** - Define resources declaratively, created on startup
- ✅ **Automatic cleanup** - Resources cleaned up after tests complete

## Installation

```bash
pip install testcontainers-aws
```

Requires:
- Python 3.8+
- Docker installed and running

## Quick Start

### Basic Usage

```python
from testcontainers_aws import AWSTestEnvironment

# Create environment with services
with AWSTestEnvironment(services=['s3', 'dynamodb', 'sqs']) as aws:
    # Get pre-configured clients
    s3 = aws.get_s3_client()
    dynamodb = aws.get_dynamodb_client()
    sqs = aws.get_sqs_client()

    # Use service helper methods
    aws.s3.create_bucket('test-bucket')
    aws.s3.put_object('test-bucket', 'key.txt', b'Hello World')

    # Use boto3 clients directly
    response = s3.get_object(Bucket='test-bucket', Key='key.txt')
    print(response['Body'].read())  # b'Hello World'
```

### With Auto-Initialization

```python
# Define resources upfront - created automatically
with AWSTestEnvironment(
    services=['s3', 'dynamodb', 'sqs'],
    init_config={
        's3_buckets': ['uploads', 'archives'],
        'dynamodb_tables': [
            {
                'name': 'users',
                'key_schema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
                'attribute_definitions': [{'AttributeName': 'id', 'AttributeType': 'S'}]
            }
        ],
        'sqs_queues': ['notifications', 'tasks']
    }
) as aws:
    # Everything is ready to use
    aws.s3.put_object('uploads', 'file.txt', b'data')
    aws.dynamodb.put_item('users', {'id': {'S': '123'}, 'name': {'S': 'Alice'}})
```

### With Pytest

```python
import pytest
from testcontainers_aws.fixtures import aws_environment, s3_bucket

def test_s3_operations(aws_environment):
    """Test with session-scoped environment (shared across tests)."""
    s3 = aws_environment.get_s3_client()
    aws_environment.s3.create_bucket('test-bucket')

    # Your test code
    aws_environment.s3.put_object('test-bucket', 'test.txt', b'content')
    assert s3.list_objects_v2(Bucket='test-bucket')['KeyCount'] == 1

def test_with_auto_cleanup_bucket(s3_bucket, aws_environment):
    """Test with function-scoped bucket (auto-created and cleaned up)."""
    aws_environment.s3.put_object(s3_bucket, 'file.txt', b'data')

    # Bucket is automatically deleted after test
```

## Supported Services

| Service | Client Method | Helper Property |
|---------|--------------|-----------------|
| S3 | `get_s3_client()` | `aws.s3` |
| DynamoDB | `get_dynamodb_client()` | `aws.dynamodb` |
| SQS | `get_sqs_client()` | `aws.sqs` |
| Kinesis | `get_kinesis_client()` | `aws.kinesis` |
| SNS | `get_sns_client()` | `aws.sns` |
| Lambda | `get_lambda_client()` | `aws.lambda_` |

## Service Helpers

### S3 Operations

```python
# Create bucket
aws.s3.create_bucket('my-bucket')

# Upload object
aws.s3.put_object('my-bucket', 'path/file.txt', b'content')

# Download object
response = aws.s3.get_object('my-bucket', 'path/file.txt')

# Delete bucket (with force to delete all objects)
aws.s3.delete_bucket('my-bucket', force=True)

# List all buckets
buckets = aws.s3.list_buckets()
```

### DynamoDB Operations

```python
# Create table
aws.dynamodb.create_table(
    name='users',
    key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
    attribute_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
)

# Put item
aws.dynamodb.put_item('users', {'id': {'S': '123'}, 'name': {'S': 'Alice'}})

# Get item
item = aws.dynamodb.get_item('users', {'id': {'S': '123'}})

# Query table
results = aws.dynamodb.query(
    'users',
    'id = :id',
    {':id': {'S': '123'}}
)

# List all tables
tables = aws.dynamodb.list_tables()
```

### SQS Operations

```python
# Create queue
response = aws.sqs.create_queue('my-queue')
queue_url = response['QueueUrl']

# Send message
aws.sqs.send_message(queue_url, 'Hello from SQS')

# Receive messages
messages = aws.sqs.receive_messages(queue_url, max_messages=10)

# Delete message
for msg in messages:
    aws.sqs.delete_message(queue_url, msg['ReceiptHandle'])

# List queues
queues = aws.sqs.list_queues()
```

### Kinesis Operations

```python
# Create stream
aws.kinesis.create_stream('my-stream', shard_count=1)

# Put record
aws.kinesis.put_record('my-stream', b'data', partition_key='key1')

# Put multiple records
aws.kinesis.put_records('my-stream', [
    {'Data': b'record1', 'PartitionKey': 'key1'},
    {'Data': b'record2', 'PartitionKey': 'key2'}
])

# Get shard iterator
shard_iterator = aws.kinesis.get_shard_iterator(
    'my-stream',
    'shardId-000000000000',
    'TRIM_HORIZON'
)

# Get records
records = aws.kinesis.get_records(shard_iterator)

# List streams
streams = aws.kinesis.list_streams()
```

### Lambda Operations

```python
from testcontainers_aws.services.lambda_service import create_lambda_zip

# Create Lambda function
code = create_lambda_zip("""
def handler(event, context):
    return {'statusCode': 200, 'body': 'Hello World'}
""")

aws.lambda_.create_function(
    function_name='my-function',
    runtime='python3.11',
    handler='index.handler',
    code=code,
    environment_variables={'ENV': 'test'}
)

# Invoke function
response = aws.lambda_.invoke_function(
    'my-function',
    payload={'key': 'value'}
)

result = json.loads(response['Payload'].read())

# Update function code
new_code = create_lambda_zip("def handler(event, context): return {'updated': True}")
aws.lambda_.update_function_code('my-function', new_code)

# List functions
functions = aws.lambda_.list_functions()

# Delete function
aws.lambda_.delete_function('my-function')
```

### SNS Operations

```python
# Create topic
response = aws.sns.create_topic('notifications')
topic_arn = response['TopicArn']

# Publish message
aws.sns.publish(
    topic_arn=topic_arn,
    message='Hello from SNS!',
    subject='Notification'
)

# Subscribe SQS queue to topic
aws.sns.subscribe(
    topic_arn=topic_arn,
    protocol='sqs',
    endpoint='arn:aws:sqs:us-east-1:000000000000:my-queue'
)

# Subscribe Lambda to topic
aws.sns.subscribe(
    topic_arn=topic_arn,
    protocol='lambda',
    endpoint='arn:aws:lambda:us-east-1:000000000000:function:my-function'
)

# Publish batch messages
aws.sns.publish_batch(
    topic_arn=topic_arn,
    messages=[
        {'Id': '1', 'Message': 'First message'},
        {'Id': '2', 'Message': 'Second message'}
    ]
)

# Get topic attributes
attributes = aws.sns.get_topic_attributes(topic_arn)

# List topics
topics = aws.sns.list_topics()

# List subscriptions
subscriptions = aws.sns.list_subscriptions_by_topic(topic_arn)

# Delete topic
aws.sns.delete_topic(topic_arn)
```

## Pytest Fixtures

testcontainers-aws provides several built-in fixtures:

```python
from testcontainers_aws.fixtures import (
    aws_environment,           # Session-scoped AWS environment
    aws_environment_function,  # Function-scoped AWS environment
    s3_client,                 # Session-scoped S3 client
    dynamodb_client,           # Session-scoped DynamoDB client
    sqs_client,                # Session-scoped SQS client
    kinesis_client,            # Session-scoped Kinesis client
    lambda_client,             # Session-scoped Lambda client
    sns_client,                # Session-scoped SNS client
    s3_bucket,                 # Function-scoped bucket (auto-cleanup)
    dynamodb_table,            # Function-scoped table (auto-cleanup)
    sqs_queue,                 # Function-scoped queue (auto-cleanup)
    kinesis_stream,            # Function-scoped stream (auto-cleanup)
    lambda_function,           # Function-scoped Lambda function (auto-cleanup)
    sns_topic,                 # Function-scoped SNS topic (auto-cleanup)
)
```

### Custom Fixtures

Create your own fixtures for common patterns:

```python
import pytest
from testcontainers_aws import AWSTestEnvironment

@pytest.fixture(scope='session')
def aws_with_data():
    """Custom fixture with pre-seeded data."""
    with AWSTestEnvironment(
        services=['dynamodb'],
        init_config={
            'dynamodb_tables': [
                {
                    'name': 'users',
                    'key_schema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
                    'attribute_definitions': [{'AttributeName': 'id', 'AttributeType': 'S'}]
                }
            ]
        }
    ) as aws:
        # Seed test data
        for i in range(10):
            aws.dynamodb.put_item('users', {
                'id': {'S': f'user-{i}'},
                'name': {'S': f'User {i}'}
            })

        yield aws
```

## Configuration

### Specify LocalStack Version

By default, testcontainers-aws uses LocalStack `4.14`. Starting with `2026.03.0`, LocalStack images
(including `latest`) require a `LOCALSTACK_AUTH_TOKEN` to start, so `4.14` is the last release that
works without an account.

If you have a LocalStack auth token, set the `LOCALSTACK_AUTH_TOKEN` environment variable and specify
the desired version:

```bash
export LOCALSTACK_AUTH_TOKEN="your-token"
```

```python
with AWSTestEnvironment(
    services=['s3'],
    image_tag='latest'  # or a specific version like '4.15'
) as aws:
    # ...
```

### Access Container Details

```python
with AWSTestEnvironment(services=['s3']) as aws:
    # Get endpoint URL
    endpoint = aws.endpoint_url
    print(f"LocalStack running at: {endpoint}")
```

## Examples

See the [examples/](examples/) directory for complete working examples:

- `basic_usage.py` - Simple S3 operations
- `pytest_example.py` - Pytest integration examples
- `auto_init.py` - Auto-initialization patterns
- `lambda_example.py` - Lambda function creation and invocation
- `sns_example.py` - SNS topics, publishing, and subscriptions
- `lambda_sns_integration.py` - Event-driven architecture with Lambda and SNS

## Real-World Use Cases

### Testing S3 Upload/Download Logic

```python
def test_file_storage_service(aws_environment):
    storage = FileStorageService(
        s3_client=aws_environment.get_s3_client(),
        bucket='uploads'
    )

    aws_environment.s3.create_bucket('uploads')

    # Test upload
    storage.upload_file('test.txt', b'content')

    # Test download
    data = storage.download_file('test.txt')
    assert data == b'content'
```

### Testing DynamoDB Repository

```python
def test_user_repository(aws_environment):
    # Create table
    aws_environment.dynamodb.create_table(
        name='users',
        key_schema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
        attribute_definitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}]
    )

    repo = UserRepository(aws_environment.get_dynamodb_client())

    # Test operations
    repo.create_user('123', 'Alice')
    user = repo.get_user('123')
    assert user['name'] == 'Alice'
```

### Testing Event-Driven Architecture

```python
def test_event_processor(aws_environment):
    from testcontainers_aws.services.lambda_service import create_lambda_zip

    # Create SNS topic
    topic_response = aws_environment.sns.create_topic('events')
    topic_arn = topic_response['TopicArn']

    # Create Lambda processor
    code = create_lambda_zip("""
def handler(event, context):
    for record in event.get('Records', []):
        # Process SNS message
        message = record['Sns']['Message']
        print(f'Processing: {message}')
    return {'statusCode': 200}
""")

    aws_environment.lambda_.create_function(
        function_name='event-processor',
        runtime='python3.11',
        handler='index.handler',
        code=code
    )

    # Subscribe Lambda to SNS
    lambda_arn = 'arn:aws:lambda:us-east-1:000000000000:function:event-processor'
    aws_environment.sns.subscribe(
        topic_arn=topic_arn,
        protocol='lambda',
        endpoint=lambda_arn
    )

    # Publish event
    aws_environment.sns.publish(
        topic_arn=topic_arn,
        message='{"type": "user_created", "user_id": "123"}'
    )
```

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details. In short:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest tests/`
5. Submit a pull request

## Development Setup

```bash
# Clone repository
git clone https://github.com/manojkken/testcontainers-aws.git
cd testcontainers-aws

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Format code
black testcontainers_aws tests

# Type checking
mypy testcontainers_aws
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Built on top of:
- [testcontainers-python](https://github.com/testcontainers/testcontainers-python)
- [LocalStack](https://github.com/localstack/localstack)
- [boto3](https://github.com/boto/boto3)

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/manojkken/testcontainers-aws/issues)
- Documentation: [Full API documentation](https://github.com/manojkken/testcontainers-aws#readme)

---

Made with ❤️ for the AWS testing community
