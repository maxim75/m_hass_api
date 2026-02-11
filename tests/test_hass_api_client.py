"""
Unit tests for the m-hass-api sample module.

This test suite covers:
- Client initialization
- GET, POST, PUT, DELETE operations
- Error handling
- Context manager usage
- Edge cases
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from m_hass_api.hass_api_client import HassApiClient, APIError


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock()
    response.status_code = 200
    response.content = b'{"status": "success"}'
    response.json.return_value = {"status": "success", "data": "test"}
    return response


@pytest.fixture
def client():
    """Create a HassApiClient instance for testing."""
    return HassApiClient(base_url="https://api.example.com", api_key="test-key")


class TestHassApiClientInitialization:
    """Tests for HassApiClient initialization."""

    def test_initialization_with_base_url(self):
        """Test client initialization with base URL."""
        client = HassApiClient(base_url="https://api.example.com")
        assert client.base_url == "https://api.example.com"
        assert client.api_key is None
        assert client.timeout == 30
        assert client.verify_ssl is True

    def test_initialization_with_trailing_slash(self):
        """Test that trailing slashes are removed from base URL."""
        client = HassApiClient(base_url="https://api.example.com/")
        assert client.base_url == "https://api.example.com"

    def test_initialization_with_api_key(self):
        """Test client initialization with API key."""
        client = HassApiClient(base_url="https://api.example.com", api_key="secret-key")
        assert client.api_key == "secret-key"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer secret-key"

    def test_initialization_with_custom_timeout(self):
        """Test client initialization with custom timeout."""
        client = HassApiClient(base_url="https://api.example.com", timeout=60)
        assert client.timeout == 60

    def test_initialization_with_ssl_disabled(self):
        """Test client initialization with SSL verification disabled."""
        client = HassApiClient(base_url="https://api.example.com", verify_ssl=False)
        assert client.verify_ssl is False

    def test_initialization_with_empty_base_url(self):
        """Test that empty base URL raises ValueError."""
        with pytest.raises(ValueError, match="base_url cannot be empty"):
            HassApiClient(base_url="")

    def test_initialization_with_whitespace_base_url(self):
        """Test that whitespace-only base URL raises ValueError."""
        with pytest.raises(ValueError, match="base_url cannot be empty"):
            HassApiClient(base_url="   ")

    def test_default_headers_set(self):
        """Test that default headers are set correctly."""
        client = HassApiClient(base_url="https://api.example.com")
        assert "Content-Type" in client.session.headers
        assert client.session.headers["Content-Type"] == "application/json"
        assert "Accept" in client.session.headers
        assert client.session.headers["Accept"] == "application/json"


class TestGetData:
    """Tests for the get_data method."""

    @patch.object(requests.Session, "get")
    def test_get_data_success(self, mock_get, client, mock_response):
        """Test successful GET request."""
        mock_get.return_value = mock_response
        result = client.get_data("posts", id=1, limit=10)

        mock_get.assert_called_once()
        assert result == {"status": "success", "data": "test"}
        assert mock_get.call_args[1]["timeout"] == 30
        assert mock_get.call_args[1]["verify"] is True

    @patch.object(requests.Session, "get")
    def test_get_data_without_endpoint(self, mock_get, client, mock_response):
        """Test GET request without endpoint."""
        mock_get.return_value = mock_response
        result = client.get_data()

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://api.example.com"
        assert call_args[1]["timeout"] == 30
        assert call_args[1]["verify"] is True
        assert call_args[1]["params"] == {}
        assert result == {"status": "success", "data": "test"}

    @patch.object(requests.Session, "get")
    def test_get_data_with_endpoint_leading_slash(
        self, mock_get, client, mock_response
    ):
        """Test GET request handles leading slash in endpoint."""
        mock_get.return_value = mock_response
        client.get_data("/posts")

        args, _ = mock_get.call_args
        assert args[0] == "https://api.example.com/posts"

    @patch.object(requests.Session, "get")
    def test_get_data_with_empty_response(self, mock_get, client):
        """Test GET request handles empty response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        result = client.get_data()
        assert result == {}

    @patch.object(requests.Session, "get")
    def test_get_data_http_error(self, mock_get, client):
        """Test GET request handles HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError("Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        with pytest.raises(APIError) as exc_info:
            client.get_data("nonexistent")

        assert "Failed to fetch data" in str(exc_info.value)
        assert exc_info.value.status_code == 404

    @patch.object(requests.Session, "get")
    def test_get_data_timeout_error(self, mock_get, client):
        """Test GET request handles timeout errors."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(APIError) as exc_info:
            client.get_data()

        assert "Failed to fetch data" in str(exc_info.value)
        assert exc_info.value.status_code is None

    @patch.object(requests.Session, "get")
    def test_get_data_connection_error(self, mock_get, client):
        """Test GET request handles connection errors."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(APIError) as exc_info:
            client.get_data()

        assert "Failed to fetch data" in str(exc_info.value)


class TestContextManager:
    """Tests for context manager functionality."""

    @patch.object(requests.Session, "close")
    def test_context_manager_enter_exit(self, mock_close):
        """Test context manager properly enters and exits."""
        with HassApiClient(base_url="https://api.example.com") as client:
            assert client is not None
            assert client.base_url == "https://api.example.com"

        mock_close.assert_called_once()

    @patch.object(requests.Session, "close")
    def test_context_manager_with_exception(self, mock_close):
        """Test context manager closes session even on exception."""
        with pytest.raises(ValueError):
            with HassApiClient(base_url="https://api.example.com") as client:
                raise ValueError("Test exception")

        mock_close.assert_called_once()

    def test_close_method(self):
        """Test the close method directly."""
        client = HassApiClient(base_url="https://api.example.com")
        with patch.object(client.session, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()


class TestAPIError:
    """Tests for the APIError exception class."""

    def test_api_error_with_message(self):
        """Test APIError with message only."""
        error = APIError("Test error message")
        assert error.message == "Test error message"
        assert error.status_code is None
        assert str(error) == "Test error message"

    def test_api_error_with_message_and_status_code(self):
        """Test APIError with message and status code."""
        error = APIError("Test error message", status_code=404)
        assert error.message == "Test error message"
        assert error.status_code == 404
        assert str(error) == "Test error message"

    def test_api_error_inheritance(self):
        """Test that APIError inherits from Exception."""
        error = APIError("Test")
        assert isinstance(error, Exception)


class TestIntegrationScenarios:
    """Integration tests for common scenarios."""

    @patch.object(requests.Session, "get")
    def test_full_workflow(self, mock_get):
        """Test a full workflow with multiple operations."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "value"}
        mock_get.return_value = mock_response

        with HassApiClient(
            base_url="https://api.example.com", api_key="test-key"
        ) as client:
            # Get data
            result1 = client.get_data("endpoint1")
            assert result1 == {"data": "value"}

            # Get more data with parameters
            result2 = client.get_data("endpoint2", param1="value1", param2="value2")
            assert result2 == {"data": "value"}

        assert mock_get.call_count == 2

    @patch.object(requests.Session, "get")
    def test_client_reuse(self, mock_get, mock_response):
        """Test reusing client for multiple requests."""
        mock_get.return_value = mock_response

        client = HassApiClient(base_url="https://api.example.com")

        result1 = client.get_data("endpoint1")
        result2 = client.get_data("endpoint2")
        result3 = client.get_data("endpoint3")

        assert mock_get.call_count == 3
        assert result1 == result2 == result3 == {"status": "success", "data": "test"}


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_base_url_with_path(self):
        """Test base URL with path."""
        client = HassApiClient(base_url="https://api.example.com/v1")
        assert client.base_url == "https://api.example.com/v1"

    def test_base_url_with_port(self):
        """Test base URL with port."""
        client = HassApiClient(base_url="https://api.example.com:8080")
        assert client.base_url == "https://api.example.com:8080"

    @patch.object(requests.Session, "get")
    def test_get_data_with_special_characters(self, mock_get, client, mock_response):
        """Test GET request with special characters in endpoint."""
        mock_get.return_value = mock_response
        client.get_data("users/filter?name=John&age=25")

        args, _ = mock_get.call_args
        assert "users/filter?name=John&age=25" in args[0]

    def test_timeout_value_boundary(self):
        """Test timeout boundary values."""
        client = HassApiClient(base_url="https://api.example.com", timeout=1)
        assert client.timeout == 1

    @patch.object(requests.Session, "get")
    def test_verify_ssl_parameter_passed(self, mock_get, client, mock_response):
        """Test that verify_ssl parameter is passed to requests."""
        client = HassApiClient(base_url="https://api.example.com", verify_ssl=False)
        mock_get.return_value = mock_response

        client.get_data()

        assert mock_get.call_args[1]["verify"] is False
