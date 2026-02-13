# m-hass-api

A Python package for interacting with Home Assistant API, featuring both REST API client and real-time WebSocket state monitoring, complete with sample code, unit tests, and deployment documentation.

## Project Structure

```
m-hass-api/
├── README.md
├── setup.py
├── requirements.txt
├── .gitignore
├── m_hass_api/
│   ├── __init__.py
│   └── sample.py
└── tests/
    ├── __init__.py
    └── test_sample.py
```

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone <repository-url>
cd m-hass-api

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install the package in development mode
pip install -e .
```

### From PyPI (Production)

```bash
pip install m-hass-api
```

## Usage

### HassApiClient - REST API Client

#### Basic Example

```python
from m_hass_api import HassApiClient

# Create a client instance
client = HassApiClient(
    base_url="http://homeassistant.local:8123",
    api_key="your_long_lived_access_token",
    tz="America/New_York"
)

# Get all states as DataFrame
states_df = client.get_states()
print(states_df)

# Get specific entity state
temp = client.get_state_as_numeric("sensor.temperature")
print(f"Temperature: {temp}°C")

# Get entity attribute
next_rising = client.get_state_attribute_as_datetime("sun.sun", "next_rising")
print(f"Sun rises at: {next_rising}")

# Get state history
history_df = client.get_state_history(
    ["sensor.temperature"],
    start_time=datetime.now(tz=timezone.utc) - timedelta(hours=24)
)
print(history_df)
```

### HassStateMonitor - Real-Time WebSocket Monitor

#### Overview

`HassStateMonitor` provides real-time monitoring of Home Assistant entity state changes using WebSocket connections. It features automatic reconnection, type-safe state conversion, timezone support, thread-safe operation, and robust error handling.

#### Features

- **Real-time monitoring** - Instant notifications when entity states change
- **Automatic reconnection** - Automatically reconnects on connection loss
- **Thread-safe operation** - Safe for concurrent access with proper locking
- **Type conversion** - Automatic conversion to numeric, datetime, boolean, or integer
- **Timezone support** - Datetime fields automatically converted to your timezone
- **Graceful shutdown** - Clean shutdown with configurable timeout
- **Error isolation** - User callback errors don't crash the monitor
- **Comprehensive logging** - Full logging for debugging and monitoring

#### Basic Usage

```python
from m_hass_api.hass_state_monitor import HassStateMonitor
from zoneinfo import ZoneInfo
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Define callback for state changes
def on_state_change(event):
    print(f"\n=== State Change ====")
    print(f"Entity: {event.entity_id}")
    print(f"Type: {event.data_type}")
    print(f"Old: {event.old_state} -> New: {event.new_state}")
    print(f"Last Updated: {event.last_updated}")
    
    # Type-specific handling
    if event.data_type == 'numeric':
        if event.old_state is not None and event.new_state is not None:
            change = event.new_state - event.old_state
            print(f"Change: {change:+.2f}")
    elif event.data_type == 'datetime':
        if event.new_state:
            print(f"New value: {event.new_state.strftime('%Y-%m-%d %H:%M:%S')}")

# Create monitor
monitor = HassStateMonitor(
    hostname="ws://homeassistant.local:8123/api/websocket",
    api_key="your_long_lived_access_token",
    entities={
        "sensor.temperature": "numeric",
        "sensor.humidity": "numeric",
        "binary_sensor.door": "bool",
        "sensor.last_motion": "datetime",
        "input_text.message": "str",
        "sensor.counter": "int"
    },
    callback=on_state_change,
    tz="Australia/Sydney"
)

# Start monitoring (non-blocking)
monitor.start()

# Monitor runs in background...
# ... do other work ...

# Stop monitoring with graceful shutdown
monitor.stop(timeout=5.0)
```

#### Advanced Usage

##### Conditional Callbacks

```python
def smart_thermostat_callback(event):
    # Only process temperature changes
    if event.entity_id != "sensor.thermostat":
        return
    
    # Significant temperature change
    if event.new_state is not None and event.old_state is not None:
        change = event.new_state - event.old_state
        
        if abs(change) > 2.0:
            print(f"⚠️  Large temperature change: {change:+.1f}°C")
            # Trigger automation...
        else:
            print(f"📊 Temperature change: {change:+.1f}°C")

monitor = HassStateMonitor(
    "ws://homeassistant.local:8123/api/websocket",
    "your_token",
    {"sensor.thermostat": "numeric"},
    smart_thermostat_callback
)
```

##### Tracking Multiple Entities

```python
# Monitor multiple sensors and aggregate data
entity_states = {}

def multi_entity_callback(event):
    entity_id = event.entity_id
    new_state = event.new_state
    
    # Update tracked state
    entity_states[entity_id] = new_state
    
    # Check conditions across entities
    if entity_states.get("sensor.temperature", 0) > 25:
        if entity_states.get("binary_sensor.ac_on", False) is False:
            print("🌡️  Temperature high, turning on AC")
            # Trigger AC automation...
```

##### Error Handling in Callbacks

```python
def robust_callback(event):
    try:
        # Your callback logic here
        process_event(event)
    except ValueError as e:
        print(f"Invalid value in event: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Note: This won't crash the monitor!
        # Errors are caught and logged automatically

monitor = HassStateMonitor(..., callback=robust_callback)
```

#### API Reference

##### HassStateMonitor

```python
class HassStateMonitor:
    def __init__(
        self,
        hostname: str,
        api_key: str,
        entities: Dict[str, str],
        callback: Callable[[StateChangeEvent], None],
        tz: Union[ZoneInfo, str, None] = None
    )
```

**Parameters:**
- `hostname` (str): WebSocket server URL (e.g., "ws://localhost:8123/api/websocket")
- `api_key` (str): Home Assistant long-lived access token
- `entities` (Dict[str, str]): Dictionary mapping entity IDs to data types
- `callback` (Callable): Function called on state changes
- `tz` (Union[ZoneInfo, str, None]): Timezone for datetime conversion

**Methods:**
- `start()` - Start monitoring (non-blocking)
- `stop(timeout: float = 5.0)` - Stop monitoring with graceful shutdown

##### StateChangeEvent

```python
@dataclass
class StateChangeEvent:
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
```

#### Data Types

| Type | Aliases | Conversion | Example |
|------|----------|-------------|---------|
| Numeric | "numeric" | `float(value)` | 23.5 |
| String | "str", "string" | `str(value)` | "hello" |
| Boolean | "bool", "boolean" | on/true/1 → True, off/false/0 → False | True |
| Integer | "int", "integer" | `int(float(value))` | 42 |
| Datetime | "datetime" | ISO 8601 to datetime with timezone | 2024-02-14 10:30:00+11:00 |

#### Configuration Examples

##### Different Timezones

```python
from zoneinfo import ZoneInfo

# Using string timezone
monitor = HassStateMonitor(..., tz="UTC")

# Using ZoneInfo object
monitor = HassStateMonitor(..., tz=ZoneInfo("America/Los_Angeles"))

# No timezone conversion (keep original)
monitor = HassStateMonitor(..., tz=None)
```

##### WebSocket URLs

```python
# Standard WebSocket (ws://)
monitor = HassStateMonitor(
    hostname="ws://192.168.1.100:8123/api/websocket",
    ...
)

# Secure WebSocket (wss://) - ensure hostname includes wss://
monitor = HassStateMonitor(
    hostname="wss://homeassistant.example.com/api/websocket",
    ...
)

# Hostname only (auto-appends /api/websocket)
monitor = HassStateMonitor(
    hostname="homeassistant.local:8123",
    ...
)
```

#### Best Practices

1. **Always configure logging** to see connection status and errors:
   ```python
   logging.basicConfig(level=logging.INFO)
   ```

2. **Use graceful shutdown** to ensure clean thread termination:
   ```python
   try:
       monitor.start()
       # ... monitoring ...
   finally:
       monitor.stop(timeout=5.0)
   ```

3. **Handle exceptions in callbacks** even though they're isolated:
   ```python
   def callback(event):
       try:
           process(event)
       except Exception as e:
           logger.error(f"Callback error: {e}")
   ```

4. **Use appropriate data types** for reliable conversions:
   ```python
   entities = {
       "sensor.temperature": "numeric",    # Numbers
       "sensor.last_seen": "datetime",     # Timestamps
       "binary_sensor.door": "bool",       # on/off states
       "sensor.count": "int",              # Whole numbers
       "sensor.text": "str"                # Text values
   }
   ```

5. **Validate API key** before starting monitor:
   ```python
   if not api_key or len(api_key) < 10:
       raise ValueError("Invalid API key")
   ```

### Running the Sample Script

```bash
# Activate your virtual environment first
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate  # On Windows

# Run the sample
python -m m_hass_api.hass_api_client
```

## Testing

### Running All Tests

```bash
# Activate your virtual environment
source venv/bin/activate  # On macOS/Linux

# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=m_hass_api --cov-report=html

# Open coverage report (macOS)
open htmlcov/index.html
```

### Running Specific Test Files

```bash
pytest tests/test_hass_api_client.py
```

### Running Specific Tests

```bash
# Run a specific test
pytest tests/test_sample.py::test_sample_client_initialization

# Run tests matching a pattern
pytest tests/ -k "test_get_data"
```

### Viewing Test Output

```bash
# Verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -v -s
```

## Development

### Project Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .
```

### Code Quality

```bash
# Format code with black
black m_hass_api/ tests/

# Check code style with flake8
flake8 m_hass_api/ tests/

# Type checking with mypy (optional)
mypy m_hass_api/
```

## CI/CD with GitHub Actions

This project uses GitHub Actions for automated testing and deployment to PyPI.

### Automated Workflow

The `.github/workflows/ci.yml` workflow provides:

- **Automated Testing**: Runs tests on multiple OS (Ubuntu, macOS, Windows) and Python versions (3.8-3.12)
- **Code Quality**: Automatic linting (flake8) and type checking (mypy)
- **Automated Building**: Builds Python packages on every push
- **Automated Publishing**: Deploys to TestPyPI and PyPI based on triggers

### Workflow Triggers

| Event | Trigger | Action |
|-------|---------|---------|
| Push to `main` | ✓ | Run tests + build package |
| Push to `develop` | ✓ | Run tests + build + publish to TestPyPI |
| Pull Request | ✓ | Run tests + build |
| GitHub Release | ✓ | Run tests + build + publish to PyPI + create release |

### Quick Start

1. **Set up PyPI account** and enable 2FA
2. **Configure trusted publishing** in PyPI settings
3. **Push to develop** to test:
   ```bash
   git push origin develop
   ```
4. **Create a release** to publish:
   ```bash
   gh release create v0.5.0 --generate-notes
   ```

For detailed setup instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Deployment

### Building the Package

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# This will create:
# - dist/m_hass_api-0.1.0.tar.gz (source distribution)
# - dist/m_hass_api-0.1.0-py3-none-any.whl (wheel)
```

### Testing the Package Locally

```bash
# Upload to TestPyPI
pip install twine
twine upload --repository testpypi dist/*

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple m-hass-api
```

### Publishing to PyPI

**Prerequisites:**
1. Create an account at https://pypi.org/account/register/
2. Enable 2-Factor Authentication
3. Generate an API token at https://pypi.org/manage/account/token/

```bash
# Upload to PyPI
twine upload dist/*

# Your package will be available at:
# https://pypi.org/project/m-hass-api/
```

### Deployment Checklist

Before deploying, ensure:
- [ ] Update version number in `setup.py`
- [ ] Update `README.md` with latest changes
- [ ] All tests pass: `pytest tests/`
- [ ] Code is formatted: `black m_hass_api/ tests/`
- [ ] No linting errors: `flake8 m_hass_api/ tests/`
- [ ] Changelog is updated (if applicable)
- [ ] Documentation is complete

### Version Management

Update the version in `setup.py` following semantic versioning:
- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

Example: `0.1.0` → `0.1.1` (patch) → `0.2.0` (minor) → `1.0.0` (major)

### GitHub Actions CI/CD (Optional)

You can automate testing and deployment with GitHub Actions. Create `.github/workflows/ci.yml`:

```yaml
name: CI/CD

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -e .
      - name: Run tests
        run: pytest tests/ --cov=m_hass_api

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/')
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install build dependencies
        run: pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## Troubleshooting

### Common Issues

**Import Error:**
```bash
# Make sure you've installed the package
pip install -e .
```

**Tests Failing:**
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
```

**Build Failing:**
```bash
# Clean and rebuild
rm -rf build/ dist/ *.egg-info
python -m build
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

MIT License - feel free to use this template for your own projects.

## Support

For issues, questions, or contributions, please open an issue on GitHub.