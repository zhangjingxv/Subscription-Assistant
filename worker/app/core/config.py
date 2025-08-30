"""
Configuration for worker processes
"""

# Import the same configuration as the API
import sys
import os

# Add the API directory to the path so we can import from it
api_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "api")
sys.path.insert(0, api_path)

from app.core.config import get_settings, Settings

__all__ = ["get_settings", "Settings"]