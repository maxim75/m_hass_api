"""
Home Assistant API client module.

This module provides a HassApiClient class that can be used to interact
with the Home Assistant API, including proper error handling, request/response
processing, and configuration management.
"""

from typing import Any, Dict, Optional
import requests


class APIError(Exception):
    """Custom exception for API-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class HassApiClient:
    """
    Home Assistant API client demonstrating best practices.

    This client provides methods to interact with the Home Assistant API,
    including proper error handling, request/response processing,
    and configuration management.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True,
    ):
        """
        Initialize the HassApiClient.

        Args:
            base_url: The base URL for the API endpoint.
            api_key: Optional API key for authentication.
            timeout: Request timeout in seconds (default: 30).
            verify_ssl: Whether to verify SSL certificates (default: True).

        Raises:
            ValueError: If base_url is empty or invalid.
        """
        if not base_url or not base_url.strip():
            raise ValueError("base_url cannot be empty")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

    def get_data(self, endpoint: str = "", **params: Any) -> Dict[str, Any]:
        """
        Retrieve data from the API.

        Args:
            endpoint: The API endpoint to call (default: "").
            **params: Query parameters to include in the request.

        Returns:
            A dictionary containing the API response data.

        Raises:
            APIError: If the API request fails or returns an error status.

        Example:
            >>> client = HassApiClient("https://api.example.com")
            >>> data = client.get_data("users", id=123, limit=10)
            >>> print(data)
        """
        endpoint = endpoint.lstrip('/')
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        try:
            response = self.session.get(url, params=params, timeout=self.timeout, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            status_code = None
            if hasattr(e, "response") and e.response is not None:
                status_code = getattr(e.response, "status_code", None)
            raise APIError(f"Failed to fetch data from {url}: {str(e)}", status_code) from e


    def close(self) -> None:
        """Close the session and clean up resources."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

