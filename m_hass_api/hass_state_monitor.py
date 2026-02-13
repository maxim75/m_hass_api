import websocket
import json
import threading
import time
from datetime import datetime

class HassStateMonitor:
    def __init__(self, hostname, api_key, entities, callback):
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
        
    def start(self):
        self.should_reconnect = True
        self.ws_thread = threading.Thread(target=self._connect)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
    def stop(self):
        self.should_reconnect = False
        if self.ws:
            self.ws.close()
        self.subscription_ids.clear()
            
    def _connect(self):
        ws_url = f"ws://{self.hostname}/api/websocket"
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        self.ws.run_forever()
        
    def _on_open(self, ws):
        print("Connected to Home Assistant")
        
    def _on_message(self, ws, message):
        msg = json.loads(message)
        
        if msg['type'] == 'auth_required':
            ws.send(json.dumps({
                'type': 'auth',
                'access_token': self.api_key
            }))
        elif msg['type'] == 'auth_ok':
            print("Authentication successful")
            self._subscribe_to_entities(ws)
        elif msg['type'] == 'result':
            if msg['success']:
                print(f"Subscription successful for ID {msg['id']}")
            else:
                print(f"Subscription failed for ID {msg['id']}: {msg.get('error')}")
        elif msg['type'] == 'event':
            self._handle_state_change(msg)
            
    def _subscribe_to_entities(self, ws):
        for entity_id in self.entity_ids:
            subscription_id = self.message_id
            self.subscription_ids[subscription_id] = entity_id
            
            ws.send(json.dumps({
                'id': subscription_id,
                'type': 'subscribe_trigger',
                'trigger': {
                    'platform': 'state',
                    'entity_id': entity_id
                }
            }))
            
            print(f"Subscribed to {entity_id} with ID {subscription_id}")
            self.message_id += 1
    
    def _convert_value(self, value, data_type):
        if value is None or value in ['unknown', 'unavailable']:
            return None
        
        try:
            if data_type == 'numeric':
                return float(value)
            elif data_type == 'datetime':
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
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
            
    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        print("Disconnected from Home Assistant")
        self.subscription_ids.clear()
        if self.should_reconnect:
            print("Reconnecting in 5 seconds...")
            time.sleep(5)
            self._connect()
            
    def _handle_state_change(self, message):
        subscription_id = message['id']
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
        
        self.callback({
            'entity_id': entity_id,
            'subscription_id': subscription_id,
            'data_type': data_type,
            'new_state': new_state,
            'old_state': old_state,
            'new_state_raw': to_state['state'] if to_state else None,
            'old_state_raw': from_state['state'] if from_state else None,
            'new_attributes': to_state['attributes'] if to_state else None,
            'old_attributes': from_state['attributes'] if from_state else None,
            'last_changed': to_state['last_changed'] if to_state else None,
            'last_updated': to_state['last_updated'] if to_state else None,
            'for_duration': trigger.get('for')
        })
