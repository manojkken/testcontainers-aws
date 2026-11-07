"""Docker-free unit tests for AWSTestEnvironment container initialization."""

from unittest.mock import Mock, patch
import pytest

from testcontainers_aws.core import AWSTestEnvironment


@pytest.fixture
def mock_container() -> Mock:
    container = Mock()
    container.with_services.return_value = container
    container.with_volume_mapping.return_value = container
    container.with_env.return_value = container
    return container


def test_auth_token_passed_to_container_when_set(
    monkeypatch: pytest.MonkeyPatch, mock_container: Mock
) -> None:
    """Verify LOCALSTACK_AUTH_TOKEN is forwarded to the container when set."""
    token = "test-secret-auth-token-12345"
    monkeypatch.setenv("LOCALSTACK_AUTH_TOKEN", token)

    with patch("testcontainers_aws.core.LocalStackContainer", return_value=mock_container) as mock_cls:
        env = AWSTestEnvironment(services=["s3"], image_tag="latest")
        env.start()

        mock_cls.assert_called_once_with(image="localstack/localstack:latest")
        mock_container.with_services.assert_called_once_with("s3")
        mock_container.with_env.assert_called_once_with("LOCALSTACK_AUTH_TOKEN", token)
        mock_container.start.assert_called_once_with()


def test_auth_token_not_passed_when_unset(
    monkeypatch: pytest.MonkeyPatch, mock_container: Mock
) -> None:
    """Verify with_env is not called when LOCALSTACK_AUTH_TOKEN is not in the environment."""
    monkeypatch.delenv("LOCALSTACK_AUTH_TOKEN", raising=False)

    with patch("testcontainers_aws.core.LocalStackContainer", return_value=mock_container) as mock_cls:
        env = AWSTestEnvironment(services=["s3"])
        env.start()

        mock_cls.assert_called_once_with(image="localstack/localstack:4.14")
        mock_container.with_services.assert_called_once_with("s3")
        mock_container.with_env.assert_not_called()
        mock_container.start.assert_called_once_with()


def test_auth_token_not_passed_when_empty_string(
    monkeypatch: pytest.MonkeyPatch, mock_container: Mock
) -> None:
    """Verify with_env is not called when LOCALSTACK_AUTH_TOKEN is empty."""
    monkeypatch.setenv("LOCALSTACK_AUTH_TOKEN", "")

    with patch("testcontainers_aws.core.LocalStackContainer", return_value=mock_container):
        env = AWSTestEnvironment(services=["s3"])
        env.start()

        mock_container.with_env.assert_not_called()
        mock_container.start.assert_called_once_with()


def test_auth_token_preserves_lambda_volume_mapping_and_services(
    monkeypatch: pytest.MonkeyPatch, mock_container: Mock
) -> None:
    """Verify services, docker volume mapping for lambda, and auth token all apply."""
    token = "test-secret-auth-token-12345"
    monkeypatch.setenv("LOCALSTACK_AUTH_TOKEN", token)

    with patch("testcontainers_aws.core.LocalStackContainer", return_value=mock_container):
        env = AWSTestEnvironment(services=["s3", "lambda"], image_tag="latest")
        env.start()

        mock_container.with_services.assert_called_once_with("s3", "lambda")
        mock_container.with_volume_mapping.assert_called_once_with(
            "/var/run/docker.sock", "/var/run/docker.sock", "rw"
        )
        mock_container.with_env.assert_called_once_with("LOCALSTACK_AUTH_TOKEN", token)
        mock_container.start.assert_called_once_with()
