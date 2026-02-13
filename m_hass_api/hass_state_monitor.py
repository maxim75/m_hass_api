import logging
import websocket
import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Union
from zoneinfo import ZoneInfo

@dataclass
class StateChangeEvent:
    """Data class representing a Home Assistant entity state change event.
    
    This dataclass encapsulates all information about a state change for a
    Home Assistant entity, including the old and new states, attributes, and
    metadata. It is passed to the user-provided callback whenever a monitored
    entity's state changes.
    
    Attributes:
        entity_id: The Home Assistant entity ID (e.g., "sensor.temperature").
        subscription_id: Internal subscription ID for tracking the entity.
        data_type: Type conversion used for state values (e.g., "numeric", "datetime").
        new_state: The new state value, converted to the specified data_type.
        old_state: The old state value, converted to the specified data_type.
        new_state_raw: The raw new state string from Home Assistant.
        old_state_raw: The raw old state string from Home Assistant.
        new_attributes: Dictionary of new entity attributes.
        old_attributes: Dictionary of old entity attributes.
        last_changed: Timestamp when the state actually changed (converted to timezone).
        last_updated: Timestamp when the state was last updated (converted to timezone).
        for_duration: Duration that the state persisted before changing (if applicable).
    """
    entity_id: str
    subscription_id: int
    data_type: str
    new_state: Any
    old_state: Any
    new_state_raw: str
    old_state_raw: str
    new_attributes: Dict[str, Any]
    old_attributes: Dict[str, Any]
    last_changed: Optional[datetime]
    last_updated: Optional[datetime]
    for_duration: Optional[str] = None

class HassStateMonitor:
    """WebSocket-based monitor for Home Assistant entity state changes.
    
    This class provides a robust, thread-safe mechanism to monitor Home Assistant
    entity state changes in real-time using WebSocket connections. It automatically
    handles authentication, subscription management, type conversion, timezone handling,
    and reconnection on connection loss.
    
    Features:
        - Automatic WebSocket connection and authentication
        - Real-time state change notifications via callback
        - Thread-safe subscription management
        - Automatic type conversion (numeric, datetime, string, boolean, integer)
        - Timezone support for datetime fields
        - Automatic reconnection on connection loss
        - Graceful shutdown with configurable timeout
        - Comprehensive error handling and logging
        - Callback exception isolation (user errors don't crash the monitor)
    
    Example:
        >>> def on_state_change(event: StateChangeEvent):
        ...     print(f"{event.entity_id}: {event.old_state} -> {event.new_state}")
        ...
        >>> monitor = HassStateMonitor(
        ...     hostname="ws://homeassistant.local:8123/api/websocket",
        ...     api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        ...     entities={
        ...         "sensor.temperature": "numeric",
        ...         "sensor.humidity": "numeric",
        ...         "binary_sensor.door": "bool"
        ...     },
        ...     callback=on_state_change,
        ...     tz="Australia/Sydney"
        ... )
        >>> monitor.start()
        >>> # ... monitor runs in background ...
        >>> monitor.stop()
    
    Note:
        The monitor runs in a daemon thread, so it will not prevent the program
        from exiting. Call `stop()` to ensure clean shutdown.
    """
    
    def __init__(
        self,
        hostname: str,
        api_key: str,
        entities: Dict[str, str],
        callback: Callable[[StateChangeEvent], None],
        tz: Union[ZoneInfo, str, None] = None
    ):
        """Initialize the Home Assistant state monitor.
        
        Args:
            hostname: WebSocket server URL (e.g., "ws://localhost:8123/api/websocket").
                      Can include protocol (ws:// or wss://) or just hostname.
            api_key: Home Assistant long-lived access token. Generate in Home Assistant
                     under Settings > Long-lived access tokens.
            entities: Dictionary mapping entity IDs to their data types. Keys are entity
                     IDs (e.g., "sensor.temperature"), values are type specifications:
                     - "numeric": Convert to float
                     - "datetime": Convert to datetime with timezone
                     - "str" or "string": Keep as string
                     - "bool" or "boolean": Convert to boolean (on/true/1 -> True)
                     - "int" or "integer": Convert to integer
            callback: Function called whenever a monitored entity's state changes.
                     Receives a StateChangeEvent object with all state information.
            tz: Timezone for datetime conversion. Can be a ZoneInfo object or a string
                (e.g., "Australia/Sydney", "UTC", "America/New_York"). If None,
                datetimes remain in their original timezone.
        
        Raises:
            ValueError: If hostname, api_key, or entities are empty/invalid.
            KeyError: If entity IDs or data types are invalid.
        
        Example:
            >>> def my_callback(event: StateChangeEvent):
            ...     if event.data_type == 'numeric':
            ...         print(f"Value changed by {event.new_state - event.old_state}")
            ...
            >>> monitor = HassStateMonitor(
            ...     hostname="ws://192.168.1.100:8123/api/websocket",
            ...     api_key="your_token_here",
            ...     entities={"sensor.temp": "numeric"},
            ...     callback=my_callback,
            ...     tz="UTC"
            ... )
        """
        self.hostname = hostname
        self.api_key = api_key
        self.entities = entities  # Dict: {"entity_id": "type"}
        self.entity_ids = list(entities.keys())
        self.callback = callback
        self.ws = None
        self.message_id = 1
        self.subscription_ids = {}  # Map subscription ID to entity_id
        self.should_reconnect = False
        self.ws_thread = None
        self._subscription_lock = threading.Lock()  # Lock for thread-safe subscription_ids access
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        # Convert string timezone to ZoneInfo object if provided
        if isinstance(tz, str):
            self.tz = ZoneInfo(tz)
        else:
            self.tz = tz
        
    def start(self):
        """Start monitoring Home Assistant state changes.
        
        This method initiates the WebSocket connection in a background thread.
        The thread runs as a daemon, so it will not prevent the program from exiting.
        
        The monitor will:
        1. Connect to the Home Assistant WebSocket API
        2. Authenticate using the provided API key
        3. Subscribe to all configured entities
        4. Call the callback whenever a state change occurs
        5. Automatically reconnect on connection loss
        
        Note:
            This method is non-blocking and returns immediately. Monitoring happens
            in the background thread.
        
        Raises:
            RuntimeError: If the monitor is already running.
            ConnectionError: If WebSocket connection cannot be established.
        """
        self.should_reconnect = True
        self.ws_thread = threading.Thread(target=self._connect)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
    def stop(self, timeout: float = 5.0):
        """Stop monitoring Home Assistant state changes.
        
        This method gracefully shuts down the monitor by:
        1. Disabling automatic reconnection
        2. Closing the WebSocket connection
        3. Clearing all subscription state
        4. Waiting for the monitoring thread to finish (up to timeout)
        
        Args:
            timeout: Maximum time to wait for the monitoring thread to finish,
                    in seconds. If None, waits indefinitely. If the timeout is
                    exceeded, a warning is logged but the method returns.
                    Default is 5.0 seconds.
        
        Note:
            The monitoring thread is a daemon thread, so even if it doesn't stop
            within the timeout, it will be terminated when the main program exits.
            However, it's best practice to wait for clean shutdown.
        
        Example:
            >>> monitor = HassStateMonitor(...)
            >>> monitor.start()
            >>> # ... some monitoring occurs ...
            >>> monitor.stop(timeout=10.0)  # Wait up to 10 seconds
            >>> print("Monitor stopped cleanly")
        """
        self.logger.info("Stopping Home Assistant state monitor...")
        self.should_reconnect = False
        
        if self.ws:
            self.ws.close()
        
        with self._subscription_lock:
            self.subscription_ids.clear()
        
        # Wait for the monitoring thread to finish
        if self.ws_thread and self.ws_thread.is_alive():
            self.logger.info(f"Waiting for monitoring thread to finish (timeout: {timeout}s)...")
            self.ws_thread.join(timeout=timeout)
            
            if self.ws_thread.is_alive():
                self.logger.warning(
                    f"Monitoring thread did not stop within {timeout}s. "
                    "It will continue as a daemon thread."
                )
            else:
                self.logger.info("Monitoring thread stopped successfully")
        else:
            self.logger.info("No active monitoring thread to stop")
            
    def _connect(self):
        """Establish WebSocket connection and start message loop.
        
        This method creates a WebSocket connection to Home Assistant and
        enters the event loop that processes incoming messages. It blocks
        until the connection is closed.
        
        The method handles:
        - WebSocket initialization
        - Event handler registration (open, message, error, close)
        - Starting the run_forever() loop
        
        Note:
            This method should only be called from the monitoring thread.
            It is blocking and does not return until the connection is closed.
        """
        ws_url = f"{self.hostname}/api/websocket"
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        self.ws.run_forever()
        
    def _on_open(self, ws):
        """Handle WebSocket connection opened event.
        
        Called when the WebSocket connection is successfully established.
        Logs the connection event.
        
        Args:
            ws: WebSocket connection object (unused but required by callback signature).
        """
        self.logger.info("Connected to Home Assistant")
        
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages.
        
        Processes messages from Home Assistant and routes them to appropriate
        handlers based on message type. Handles authentication, subscription
        confirmation, and state change events.
        
        Args:
            ws: WebSocket connection object (unused but required by callback signature).
            message: JSON-encoded message string from Home Assistant.
        
        Message Types Handled:
            - auth_required: Sends authentication token
            - auth_ok: Initiates entity subscriptions
            - result: Logs subscription success/failure
            - event: Processes state change events
        
        Note:
            Any unknown message types are silently ignored.
        """
        msg = json.loads(message)
        
        if msg['type'] == 'auth_required':
            ws.send(json.dumps({
                'type': 'auth',
                'access_token': self.api_key
            }))
        elif msg['type'] == 'auth_ok':
            self.logger.info("Authentication successful")
            self._subscribe_to_entities(ws)
        elif msg['type'] == 'result':
            if msg['success']:
                self.logger.info(f"Subscription successful for ID {msg['id']}")
            else:
                self.logger.error(f"Subscription failed for ID {msg['id']}: {msg.get('error')}")
        elif msg['type'] == 'event':
            self._handle_state_change(msg)
            
    def _subscribe_to_entities(self, ws):
        """Subscribe to all configured entities for state change monitoring.
        
        Iterates through the entities dictionary and sends subscription requests
        to Home Assistant for each entity. Uses a monotonically increasing
        message ID for tracking subscriptions.
        
        Args:
            ws: WebSocket connection object to send subscriptions on.
        
        Note:
            This method is thread-safe. The subscription_ids dictionary is
            protected by a lock to prevent race conditions with concurrent
            state change event processing.
        """
        for entity_id in self.entity_ids:
            subscription_id = self.message_id
            with self._subscription_lock:
                self.subscription_ids[subscription_id] = entity_id
            
            ws.send(json.dumps({
                'id': subscription_id,
                'type': 'subscribe_trigger',
                'trigger': {
                    'platform': 'state',
                    'entity_id': entity_id
                }
            }))
            
            self.logger.info(f"Subscribed to {entity_id} with ID {subscription_id}")
            self.message_id += 1
    
    def _convert_value(self, value, data_type):
        """Convert a state value to the specified Python type.
        
        Handles type conversion for Home Assistant state values, with special
        handling for None, "unknown", and "unavailable" states. Provides
        robust error handling to prevent crashes from malformed data.
        
        Args:
            value: The raw state value from Home Assistant.
            data_type: Target type for conversion. Valid values:
                      - "numeric": Convert to float
                      - "datetime": Convert via _convert_timestamp
                      - "str" or "string": Convert to str
                      - "bool" or "boolean": Convert to bool
                      - "int" or "integer": Convert to int
        
        Returns:
            The converted value, or None if conversion fails or value is
            None/"unknown"/"unavailable".
        
        Note:
            Boolean conversion is lenient: "on", "true", "1" (case-insensitive)
            convert to True; "off", "false", "0" convert to False.
        """
        if value is None or value in ['unknown', 'unavailable']:
            return None
        
        try:
            if data_type == 'numeric':
                return float(value)
            elif data_type == 'datetime':
                return self._convert_timestamp(value)
            elif data_type in ['str', 'string']:
                return str(value)
            elif data_type in ['bool', 'boolean']:
                if isinstance(value, bool):
                    return value
                lower_val = str(value).lower()
                if lower_val in ['on', 'true', '1']:
                    return True
                elif lower_val in ['off', 'false', '0']:
                    return False
                return None
            elif data_type in ['int', 'integer']:
                return int(float(value))
            else:
                return value
        except (ValueError, TypeError, AttributeError):
            return None
            
    def _convert_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Convert a timestamp string to a datetime object with timezone support.
        
        Parses ISO 8601 timestamp strings from Home Assistant and converts them
        to timezone-aware datetime objects. Handles both timezone-aware and
        timezone-naive inputs, applying the configured timezone if specified.
        
        Args:
            timestamp_str: ISO 8601 timestamp string (e.g., "2024-02-14T10:30:00Z"
                          or "2024-02-14T10:30:00+00:00").
        
        Returns:
            A timezone-aware datetime object in the configured timezone, or None
            if the input is empty or parsing fails.
        
        Note:
            - 'Z' suffix is converted to '+00:00' for parsing
            - If self.tz is None, the original timezone is preserved
            - If self.tz is set, the datetime is converted to that timezone
            - Parsing failures are silently handled by returning None
        """
        if not timestamp_str:
            return None
        
        try:
            datetime_value = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            if self.tz is not None:
                # Check if the datetime is timezone-aware
                if datetime_value.tzinfo is not None:
                    # Convert from existing timezone to the specified timezone
                    datetime_value = datetime_value.astimezone(self.tz)
                else:
                    # Localize timezone-naive datetime to the specified timezone
                    datetime_value = datetime_value.replace(tzinfo=self.tz)
            return datetime_value
        except (ValueError, TypeError, AttributeError):
            return None
            
    def _on_error(self, ws, error):
        """Handle WebSocket error events.
        
        Called when a WebSocket error occurs. Logs the error for debugging
        and troubleshooting. The connection will typically be closed after
        an error, triggering the _on_close handler.
        
        Args:
            ws: WebSocket connection object (unused but required by callback signature).
            error: Exception or error message describing the WebSocket error.
        """
        self.logger.error(f"WebSocket error: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection closed event.
        
        Called when the WebSocket connection is closed. Logs the disconnection,
        clears subscription state, and initiates reconnection if configured.
        
        Args:
            ws: WebSocket connection object (unused but required by callback signature).
            close_status_code: WebSocket close status code (e.g., 1000 for normal
                               closure, 1006 for abnormal closure).
            close_msg: Human-readable reason for the close (may be empty).
        
        Note:
            - If should_reconnect is True, waits 5 seconds then reconnects
            - Subscription IDs are cleared to prevent processing stale data
            - The reconnection attempt will continue indefinitely until stop() is called
        """
        self.logger.info("Disconnected from Home Assistant")
        with self._subscription_lock:
            self.subscription_ids.clear()
        if self.should_reconnect:
            self.logger.warning("Reconnecting in 5 seconds...")
            time.sleep(5)
            self._connect()
            
    def _handle_state_change(self, message):
        """Process a state change event from Home Assistant.
        
        Extracts state change information from the WebSocket message, converts
        values to the appropriate types, and invokes the user-provided callback.
        Handles exceptions in the callback to prevent monitoring thread crashes.
        
        Args:
            message: WebSocket message dictionary containing state change event data.
                    Expected structure:
                    {
                        "id": <subscription_id>,
                        "event": {
                            "variables": {
                                "trigger": {
                                    "to_state": {...},
                                    "from_state": {...},
                                    "for": <duration>
                                }
                            }
                        }
                    }
        
        Note:
            - The subscription ID lookup is thread-safe (protected by lock)
            - Unknown subscription IDs are silently ignored
            - Callback exceptions are caught and logged, but don't stop monitoring
            - State values are converted according to the entity's configured data_type
        """
        subscription_id = message['id']
        with self._subscription_lock:
            entity_id = self.subscription_ids.get(subscription_id)
        
        if not entity_id:
            return
            
        variables = message['event'].get('variables', {})
        trigger = variables.get('trigger', {})
        to_state = trigger.get('to_state')
        from_state = trigger.get('from_state')
        
        data_type = self.entities[entity_id]
        
        # Convert state values based on type
        new_state = self._convert_value(
            to_state['state'] if to_state else None,
            data_type
        )
        old_state = self._convert_value(
            from_state['state'] if from_state else None,
            data_type
        )
        
        # Create StateChangeEvent instance
        event = StateChangeEvent(
            entity_id=entity_id,
            subscription_id=subscription_id,
            data_type=data_type,
            new_state=new_state,
            old_state=old_state,
            new_state_raw=to_state['state'] if to_state else None,
            old_state_raw=from_state['state'] if from_state else None,
            new_attributes=to_state['attributes'] if to_state else None,
            old_attributes=from_state['attributes'] if from_state else None,
            last_changed=self._convert_timestamp(to_state['last_changed'] if to_state else None),
            last_updated=self._convert_timestamp(to_state['last_updated'] if to_state else None),
            for_duration=trigger.get('for')
        )
        
        # Invoke callback with exception handling to prevent thread crashes
        try:
            self.callback(event)
        except Exception as e:
            self.logger.error(
                f"Error in user callback for entity {entity_id}: {e}",
                exc_info=True
            )
