from dotenv import load_dotenv
from m_hass_api.hass_api_client import HassApiClient
import os

load_dotenv()

HA_TOKEN = os.getenv('HA_TOKEN')
HA_HOSTNAME = os.getenv('HA_HOSTNAME')

print(HA_HOSTNAME)

client = HassApiClient(base_url=HA_HOSTNAME, api_key=HA_TOKEN)

response = client.get_data("/api/states")

print(response)
