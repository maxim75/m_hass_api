from dotenv import load_dotenv
from m_hass_api.hass_api_client import HassApiClient
import os
from zoneinfo import ZoneInfo

load_dotenv()

HA_TOKEN = os.getenv("HA_TOKEN")
HA_HOSTNAME = os.getenv("HA_HOSTNAME")

print(HA_HOSTNAME)

client = HassApiClient(
    base_url=HA_HOSTNAME, api_key=HA_TOKEN, tz=ZoneInfo("Australia/Sydney")
)

states_df = client.get_states()

print(states_df[states_df.entity_id.str.contains("red")])


# Get enity state
print("sun.sun: ", client.get_state_as_string("sun.sun"))
print("sensor.stairs_bottom_pir_last_seen: ", client.get_state_as_datetime("sensor.stairs_bottom_pir_last_seen"))
print("sensor.home_assistant_core_cpu_percent: ", client.get_state_as_numeric("sensor.home_assistant_core_cpu_percent"))

# Get entity attribute:
print("sun.sun / elevation: ", client.get_state_attribute_as_numeric("sun.sun", "elevation"))
print("sun.sun / next_setting: ", client.get_state_attribute_as_datetime("sun.sun", "next_setting"))


#history_df = client.get_state_history(["sensor.gw2000c_outdoor_temperature"])

history_df = client.get_state_history(["sensor.bus"])
print(history_df.sort_values(by="last_updated").head(20))

print(history_df.columns)
