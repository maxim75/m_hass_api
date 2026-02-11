from dotenv import load_dotenv
from m_hass_api.hass_api_client import HassApiClient
import os
from zoneinfo import ZoneInfo

load_dotenv()

HA_TOKEN = os.getenv('HA_TOKEN')
HA_HOSTNAME = os.getenv('HA_HOSTNAME')

print(HA_HOSTNAME)

client = HassApiClient(base_url=HA_HOSTNAME, api_key=HA_TOKEN, tz=ZoneInfo('Australia/Sydney'))

states_df = client.get_states()

print(states_df[states_df.entity_id.str.contains("red")])

print(client.get_state_as_string("sensor.gw2000c_outdoor_temperature"))
print(client.get_state_as_numeric("sensor.gw2000c_outdoor_temperature") > 30)

print(client.get_state_as_string("sensor.corridor_window_last_seen"))
print("df", client.get_state_as_datetime("sensor.corridor_window_last_seen").strftime("%H:%M:%S"))

history = client.get_state_history(["sensor.gw2000c_outdoor_temperature"])
print(history.head())