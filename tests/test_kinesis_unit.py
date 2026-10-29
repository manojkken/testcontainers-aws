"""Docker-free regression tests for Kinesis service manager delegation."""

from unittest.mock import Mock

from testcontainers_aws.services.kinesis import KinesisServiceManager


def make_manager():
    client = Mock()
    environment = Mock()
    environment.get_client.return_value = client
    return KinesisServiceManager(environment), client, environment


def test_kinesis_client_is_lazily_initialized_and_cached():
    manager, client, environment = make_manager()

    assert manager.client is client
    assert manager.client is client
    environment.get_client.assert_called_once_with('kinesis')


def test_create_stream_waits_for_stream_to_exist():
    manager, client, _ = make_manager()
    response = {'ResponseMetadata': {}}
    client.create_stream.return_value = response

    assert manager.create_stream('events', shard_count=2, StreamModeDetails={'StreamMode': 'PROVISIONED'}) is response
    client.create_stream.assert_called_once_with(
        StreamName='events',
        ShardCount=2,
        StreamModeDetails={'StreamMode': 'PROVISIONED'},
    )
    client.get_waiter.assert_called_once_with('stream_exists')
    client.get_waiter.return_value.wait.assert_called_once_with(StreamName='events')


def test_put_record_forwards_data_and_extra_options():
    manager, client, _ = make_manager()
    response = {'SequenceNumber': '123'}
    client.put_record.return_value = response

    assert manager.put_record('events', b'hello', 'partition', ExplicitHashKey='7') is response
    client.put_record.assert_called_once_with(
        StreamName='events', Data=b'hello', PartitionKey='partition', ExplicitHashKey='7',
    )


def test_put_records_forwards_batch_and_extra_options():
    manager, client, _ = make_manager()
    records = [{'Data': b'hello', 'PartitionKey': 'partition'}]
    response = {'FailedRecordCount': 0}
    client.put_records.return_value = response

    assert manager.put_records('events', records, StreamARN='arn:stream') is response
    client.put_records.assert_called_once_with(
        StreamName='events', Records=records, StreamARN='arn:stream',
    )


def test_get_shard_iterator_forwards_type_and_options():
    manager, client, _ = make_manager()
    client.get_shard_iterator.return_value = {'ShardIterator': 'iterator-token'}

    assert manager.get_shard_iterator('events', 'shard-1', 'LATEST', DryRun=True) == 'iterator-token'
    client.get_shard_iterator.assert_called_once_with(
        StreamName='events', ShardId='shard-1', ShardIteratorType='LATEST', DryRun=True,
    )


def test_get_records_preserves_limit_and_options():
    manager, client, _ = make_manager()
    response = {'Records': []}
    client.get_records.return_value = response

    assert manager.get_records('iterator-token', limit=5, DryRun=True) is response
    client.get_records.assert_called_once_with(ShardIterator='iterator-token', Limit=5, DryRun=True)

    manager.get_records('iterator-token')
    client.get_records.assert_called_with(ShardIterator='iterator-token')


def test_describe_and_delete_stream_preserve_responses():
    manager, client, _ = make_manager()
    client.describe_stream.return_value = {'StreamDescription': {'StreamName': 'events'}}
    client.delete_stream.return_value = {'ResponseMetadata': {}}

    assert manager.describe_stream('events') is client.describe_stream.return_value
    client.describe_stream.assert_called_once_with(StreamName='events')

    assert manager.delete_stream('events', EnforceConsumerDeletion=True) is client.delete_stream.return_value
    client.delete_stream.assert_called_once_with(StreamName='events', EnforceConsumerDeletion=True)


def test_list_streams_preserves_names_and_optional_limit():
    manager, client, _ = make_manager()
    client.list_streams.return_value = {'StreamNames': ['events', 'logs']}

    assert manager.list_streams(limit=2) == ['events', 'logs']
    client.list_streams.assert_called_once_with(Limit=2)

    client.list_streams.return_value = {}
    assert manager.list_streams() == []
    client.list_streams.assert_called_with()
