"""Kinesis service manager with helper methods."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast
from testcontainers_aws.services.base import BaseServiceManager

if TYPE_CHECKING:
    from types_boto3_kinesis import KinesisClient
    from types_boto3_kinesis.literals import ShardIteratorTypeType
    from types_boto3_kinesis.type_defs import (
        DescribeStreamOutputTypeDef,
        EmptyResponseMetadataTypeDef,
        GetRecordsOutputTypeDef,
        PutRecordOutputTypeDef,
        PutRecordsOutputTypeDef,
        PutRecordsRequestEntryTypeDef,
    )


class KinesisServiceManager(BaseServiceManager):
    """Manages Kinesis operations and simplifies common testing tasks."""

    @property
    def client(self) -> 'KinesisClient':
        """Get Kinesis client."""
        if not self._client:
            self._client = self.environment.get_client('kinesis')
        return cast('KinesisClient', self._client)

    def create_stream(
        self,
        stream_name: str,
        shard_count: int = 1,
        **kwargs: Any
    ) -> 'EmptyResponseMetadataTypeDef':
        """
        Create a Kinesis stream.

        Args:
            stream_name: Name of the stream
            shard_count: Number of shards (default: 1)
            **kwargs: Additional arguments passed to create_stream

        Returns:
            Response from create_stream API
        """
        response = self.client.create_stream(
            StreamName=stream_name,
            ShardCount=shard_count,
            **kwargs
        )

        # Streams start in CREATING state and reject writes until ACTIVE
        self.client.get_waiter('stream_exists').wait(StreamName=stream_name)

        return response

    def put_record(
        self,
        stream_name: str,
        data: bytes,
        partition_key: str,
        **kwargs: Any
    ) -> 'PutRecordOutputTypeDef':
        """
        Put a record into a Kinesis stream.

        Args:
            stream_name: Target stream name
            data: Record data (bytes)
            partition_key: Partition key for the record
            **kwargs: Additional arguments passed to put_record

        Returns:
            Response from put_record API
        """
        return self.client.put_record(
            StreamName=stream_name,
            Data=data,
            PartitionKey=partition_key,
            **kwargs
        )

    def put_records(
        self,
        stream_name: str,
        records: List[Dict[str, Any]],
        **kwargs: Any
    ) -> 'PutRecordsOutputTypeDef':
        """
        Put multiple records into a Kinesis stream.

        Args:
            stream_name: Target stream name
            records: List of records, each with 'Data' and 'PartitionKey'
            **kwargs: Additional arguments passed to put_records

        Returns:
            Response from put_records API
        """
        return self.client.put_records(
            StreamName=stream_name,
            Records=cast('List[PutRecordsRequestEntryTypeDef]', records),
            **kwargs
        )

    def get_shard_iterator(
        self,
        stream_name: str,
        shard_id: str,
        iterator_type: 'ShardIteratorTypeType' = 'TRIM_HORIZON',
        **kwargs: Any
    ) -> str:
        """
        Get a shard iterator for reading from a stream.

        Args:
            stream_name: Stream name
            shard_id: Shard ID
            iterator_type: Iterator type (default: TRIM_HORIZON)
            **kwargs: Additional arguments passed to get_shard_iterator

        Returns:
            Shard iterator string
        """
        response = self.client.get_shard_iterator(
            StreamName=stream_name,
            ShardId=shard_id,
            ShardIteratorType=iterator_type,
            **kwargs
        )
        return response['ShardIterator']

    def get_records(
        self,
        shard_iterator: str,
        limit: Optional[int] = None,
        **kwargs: Any
    ) -> 'GetRecordsOutputTypeDef':
        """
        Get records from a Kinesis stream.

        Args:
            shard_iterator: Shard iterator
            limit: Maximum number of records to retrieve
            **kwargs: Additional arguments passed to get_records

        Returns:
            Response from get_records API
        """
        params: Dict[str, Any] = {'ShardIterator': shard_iterator}

        if limit:
            params['Limit'] = limit

        params.update(kwargs)
        return self.client.get_records(**params)

    def describe_stream(self, stream_name: str) -> 'DescribeStreamOutputTypeDef':
        """
        Describe a Kinesis stream.

        Args:
            stream_name: Stream name

        Returns:
            Response from describe_stream API
        """
        return self.client.describe_stream(StreamName=stream_name)

    def delete_stream(self, stream_name: str, **kwargs: Any) -> 'EmptyResponseMetadataTypeDef':
        """
        Delete a Kinesis stream.

        Args:
            stream_name: Stream to delete
            **kwargs: Additional arguments passed to delete_stream

        Returns:
            Response from delete_stream API
        """
        return self.client.delete_stream(StreamName=stream_name, **kwargs)

    def list_streams(self, limit: Optional[int] = None) -> List[str]:
        """
        List all Kinesis streams.

        Args:
            limit: Maximum number of streams to return

        Returns:
            List of stream names
        """
        params: Dict[str, Any] = {}
        if limit:
            params['Limit'] = limit

        response = self.client.list_streams(**params)
        return response.get('StreamNames', [])
