"""
Home Assistant API client module.

This module provides a HassApiClient class that can be used to interact
with the Home Assistant API, including proper error handling, request/response
processing, and configuration management.
"""

from typing import Any, Dict, Optional, Union
import requests
import pandas as pd
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from datetime import datetime, timezone, timedelta


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
        states_df: pd.DataFrame = None,
        tz: Union[ZoneInfo, str] = None,
    ):
        """
        Initialize the HassApiClient.

        Args:
            base_url: The base URL for the API endpoint.
            api_key: Optional API key for authentication.
            timeout: Request timeout in seconds (default: 30).
            verify_ssl: Whether to verify SSL certificates (default: True).
            states_df: Optional pre-loaded DataFrame of states.
            tz: Optional timezone as either a ZoneInfo object or string
                (e.g., 'Australia/Sydney', 'UTC', 'America/New_York').

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
        self.states_df = None

        # Convert string timezone to ZoneInfo object if provided
        if isinstance(tz, str):
            self.tz = ZoneInfo(tz)
        else:
            self.tz = tz

        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

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
        endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        try:
            response = self.session.get(
                url, params=params, timeout=self.timeout, verify=self.verify_ssl
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            status_code = None
            if hasattr(e, "response") and e.response is not None:
                status_code = getattr(e.response, "status_code", None)
            raise APIError(
                f"Failed to fetch data from {url}: {str(e)}", status_code
            ) from e

    def get_states(self) -> pd.DataFrame:
        if self.states_df is None:
            states = self.get_data(f"/api/states")
            states_df = pd.DataFrame(states)
            print(f"Requests approach: {len(states)} entities")
            self.states_df = states_df
        return self.states_df

    def get_state_as_string(self, entity_id) -> str:
        states_df = self.get_states()
        state_row = states_df[states_df["entity_id"] == entity_id]
        if not state_row.empty:
            return state_row.iloc[0]["state"]
        else:
            return None
        
    def to_numeric(self, value: str) -> float:
        if value:
            return pd.to_numeric(value, errors="coerce")
        else:
            return None
        
    def to_datetime(self, value: str) -> datetime:
        if value is not None:
            datetime_value = pd.to_datetime(value, errors="coerce")
            if self.tz is not None:
                # Check if the datetime is timezone-naive
                if datetime_value.tz is None:
                    # Localize to the specified timezone
                    datetime_value = datetime_value.tz_localize(self.tz)
                else:
                    # Convert from existing timezone to the specified timezone
                    datetime_value = datetime_value.tz_convert(self.tz)
            return datetime_value
        else:
            return None

    def get_state_as_datetime(self, entity_id) -> datetime:
        return self.to_datetime(self.get_state_as_string(entity_id))
    
    def get_state_as_numeric(self, entity_id) -> float:
        return self.to_numeric(self.get_state_as_string(entity_id))
        
    def get_state_attribute_as_string(self, entity_id, attribute_name) -> str:
        if self.states_df is None:
            self.get_states()
        state_row = self.states_df[self.states_df['entity_id'] == entity_id]
        if not state_row.empty:
            attributes = state_row.iloc[0]['attributes']
            if attribute_name in attributes:
                return attributes[attribute_name]
        return None
    
    def get_state_attribute_as_datetime(self, entity_id, attribute_name) -> datetime:
        return self.to_datetime(self.get_state_attribute_as_string(entity_id, attribute_name))
    
    def get_state_attribute_as_numeric(self, entity_id, attribute_name) -> datetime:
        return self.to_numeric(self.get_state_attribute_as_string(entity_id, attribute_name))

    def get_state_history(self, entity_ids, start_time=None, end_time=None, get_attributes=False):
        if start_time is None:
            start_time = datetime.now(timezone.utc) - timedelta(days=1)
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S%z")

        query_params = {
            "filter_entity_id": ",".join(entity_ids),
        }

        if end_time is not None:
            end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S%z")
            query_params["end_time"] = end_time_str

        encoded_params = urlencode(query_params)
        # url = f"{self.hostname}/api/history/period/{start_time_str}?{encoded_params}"
        # print(url)
        response = self.get_data(
            f"/api/history/period/{start_time_str}",
            filter_entity_id=",".join(entity_ids),
        )

        dfs = []
        for part in response:
            print(part[1])
            dfs.append(pd.DataFrame(part))

        history_df = pd.concat(dfs, ignore_index=True)
        history_df["last_updated"] = pd.to_datetime(
            history_df["last_updated"], format="ISO8601"
        )
        history_df["last_changed"] = pd.to_datetime(
            history_df["last_changed"], format="ISO8601"
        )
        if self.tz is not None:
            history_df["last_updated"] = history_df["last_updated"].dt.tz_convert(
                self.tz
            )
            history_df["last_changed"] = history_df["last_changed"].dt.tz_convert(
                self.tz
            )
        
        if get_attributes:
            # Explode attributes into separate rows
            attributes_df = history_df[["entity_id", "last_updated", "last_changed", "state"]].copy()
            attributes_list = []
            for idx, row in history_df.iterrows():
                if isinstance(row["attributes"], dict):
                    for attr_name, attr_value in row["attributes"].items():
                        attributes_list.append({
                            "entity_id": row["entity_id"],
                            "last_updated": row["last_updated"],
                            "last_changed": row["last_changed"],
                            "state": row["state"],
                            "attribute_name": attr_name,
                            "attribute_value": attr_value
                        })
            history_df = pd.DataFrame(attributes_list)
        
        return history_df

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
