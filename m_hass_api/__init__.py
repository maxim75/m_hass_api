"""
m-hass-api: A Python package for interacting with Home Assistant API.

This package provides a HassApiClient that demonstrates best practices for:
- Package structure
- Error handling
- Unit testing
- Documentation
- Deployment
"""

__version__ = "0.1.0"
__author__ = "Maksym Kozlenko"
__email__ = "max@kozlenko.info"

from m_hass_api.hass_api_client import HassApiClient

__all__ = ["HassApiClient", "__version__"]
