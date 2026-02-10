# Quick Start Guide for m-hass-api

This guide will help you get up and running with the m-hass-api package in minutes.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Option 1: Install in Development Mode (Recommended for Developers)

```bash
# Navigate to the project directory
cd m-hass-api

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install the package in editable mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt
```

### Option 2: Install from PyPI (When Published)

```bash
pip install m-hass-api
```

## Quick Examples

### Example 1: Basic Usage

```python
from m_hass_api import HassApiClient

# Create a client
client = HassApiClient(base_url="https://jsonplaceholder.typicode.com")

# Get data
posts = client.get_data("posts", _limit=5)
print(f"Retrieved {len(posts)} posts")

# Close the client when done
client.close()
```

### Example 2: Using Context Manager

```python
from m_hass_api import HassApiClient

# Use context manager for automatic cleanup
with HassApiClient(base_url="https://jsonplaceholder.typicode.com") as client:
    users = client.get_data("users", _limit=3)
    for user in users:
        print(f"{user['name']} - {user['email']}")
```

### Example 3: With API Key

```python
from m_hass_api import HassApiClient

# Create client with authentication
client = HassApiClient(
    base_url="https://api.example.com",
    api_key="your-api-key-here",
    timeout=60
)

# Make authenticated requests
data = client.get_data("protected-endpoint")

# Close when done
client.close()
```

## Running the Demo

The package includes a built-in demo that you can run to see it in action:

```bash
# Make sure your virtual environment is activated
source venv/bin/activate  # On macOS/Linux

# Run the demo
python -m m_hass_api

# Or using the console script (if installed)
m-hass-api
```

## Running Tests

```bash
# Activate your virtual environment
source venv/bin/activate  # On macOS/Linux

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=m_hass_api --cov-report=html

# Open the coverage report (macOS)
open htmlcov/index.html
```

## Common Commands

### Development

```bash
# Format code with black
black m_hass_api/ tests/

# Check code style
flake8 m_hass_api/ tests/

# Type checking (optional)
mypy m_hass_api/
```

### Building the Package

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# The built files will be in the dist/ directory
```

### Publishing to PyPI

```bash
# Upload to TestPyPI first (for testing)
twine upload --repository testpypi dist/*

# Upload to PyPI (production)
twine upload dist/*
```

## Project Structure

```
m-hass-api/
├── README.md              # Full documentation
├── QUICKSTART.md          # This file
├── setup.py               # Package configuration
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore patterns
├── m_hass_api/           # Main package directory
│   ├── __init__.py       # Package initialization
│   ├── __main__.py       # Entry point for `python -m m_hass_api`
│   └── sample.py         # Sample API client implementation
└── tests/                # Test suite
    ├── __init__.py
    └── test_sample.py     # Unit tests
```

## Next Steps

1. **Customize the package**: Edit the files to match your needs
   - Update `setup.py` with your package details
   - Modify `m_hass_api/sample.py` to implement your API client
   - Add tests in `tests/test_sample.py`

2. **Read the full documentation**: See `README.md` for detailed information on:
   - Advanced usage
   - Error handling
   - Deployment procedures
   - CI/CD setup

3. **Start coding**: Use the sample code as a template for your own implementation

## Getting Help

- Check the `README.md` for comprehensive documentation
- Run the demo to see the package in action: `python -m m_hass_api`
- Run the tests to ensure everything works: `pytest tests/ -v`

## Tips

- Always use a virtual environment for development
- Run tests before committing changes
- Use the context manager pattern for automatic resource cleanup
- Check the README for deployment instructions before publishing to PyPI