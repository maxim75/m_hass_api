"""
Setup configuration for m-hass-api package.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="m-hass-api",
    version="0.4.0",
    author="Maksym Kozlenko",
    author_email="max@kozlenko.info",
    description="Python package for Home Assistant API with real-time WebSocket state monitoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/maxim75/m-hass-api",
    project_urls={
        "Bug Tracker": "https://github.com/maxim75/m-hass-api/issues",
        "Documentation": "https://github.com/maxim75/m-hass-api/blob/main/README.md",
        "Source Code": "https://github.com/maxim75/m-hass-api",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "websocket-client>=1.0.0",
        "python-dotenv>=0.19.0",
        "pandas>=1.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=21.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    keywords="home-assistant api websocket rest client home automation",
    entry_points={
        "console_scripts": [
            "m-hass-api=m_hass_api.run:main",
        ],
    },
)