# m-hass-api

A Python package for interacting with Home Assistant API, complete with sample code, unit tests, and deployment documentation.

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

### Basic Example

```python
from m_hass_api import HassApiClient

# Create a client instance
client = HassApiClient(base_url="https://api.example.com")

# Make a sample API call
result = client.get_data()
print(f"Result: {result}")

# Get data with parameters
filtered_result = client.get_data(param1="value1", param2="value2")
print(f"Filtered Result: {filtered_result}")
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