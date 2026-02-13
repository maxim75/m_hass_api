from dotenv import load_dotenv
from m_hass_api.hass_api_client import HassApiClient
from m_hass_api.hass_state_monitor import HassStateMonitor
import os
from datetime import datetime, timedelta, UTC
from zoneinfo import ZoneInfo
from time import sleep

load_dotenv()

HA_TOKEN = os.getenv("HA_TOKEN")
HA_HOSTNAME = os.getenv("HA_HOSTNAME")

print(HA_HOSTNAME)

client = HassApiClient(
    base_url=HA_HOSTNAME, api_key=HA_TOKEN, tz=ZoneInfo("Australia/Sydney")
)

# get all states as DataFrame
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

history_df = client.get_state_history(["sensor.gw2000c_outdoor_temperature"], get_attributes=False, start_time=datetime.now(UTC) - timedelta(hours=1))
#history_df = history_df[history_df.attribute_name == "elevation"]
#history_df.attribute_value = history_df.attribute_value.astype(float)
print(history_df.sort_values(by="last_updated")[["last_updated", "state"]].head(40))

print(history_df.columns)

# Usage example:
def on_state_change(state_change):
    print(f"Entity {state_change.entity_id} ({state_change.data_type}) changed:")
    print(f"  Old state: {state_change.old_state} (type: {type(state_change.old_state).__name__})")
    print(f"  New state: {state_change.new_state} (type: {type(state_change.new_state).__name__})")
    print(f"  Raw old: {state_change.old_state_raw}")
    print(f"  Raw new: {state_change.new_state_raw}")
    print(f" last_updated: {state_change.last_updated}")
    
    # Example: Type-specific handling
    if state_change.data_type == 'numeric':
        if state_change.new_state is not None and state_change.old_state is not None:
            change = state_change.new_state - state_change.old_state
            print(f"  Numeric change: {'+' if change > 0 else ''}{change}")
    elif state_change.data_type == 'datetime':
        if state_change.new_state is not None and state_change.old_state is not None:
            diff = state_change.new_state - state_change.old_state
            print(f"  Time difference: {diff}")


monitor = HassStateMonitor(
    HA_HOSTNAME.replace("http://", ""),
    HA_TOKEN,
    {
        "sensor.rumpus_tv_gpo_last_seen": 'datetime',
        "input_text.nrf_message": "str"
    },
    on_state_change,
    tz=ZoneInfo("Australia/Sydney")
)

monitor.start()
sleep(60)
monitor.stop()
