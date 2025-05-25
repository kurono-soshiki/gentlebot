"""
Configuration for running pytest.

This file is automatically loaded by pytest to configure the test environment.
"""
import os
import sys
import pytest

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    Mock environment variables for testing.
    
    This fixture provides a way to mock environment variables for testing
    without affecting the actual environment.
    """
    # Define default mock environment variables
    env_vars = {
        "DISCORD_TOKEN": "mock_discord_token",
        "GEMINI_API_KEY": "mock_gemini_api_key",
    }
    
    # Set environment variables
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
        
    return env_vars