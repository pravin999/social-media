"""Pytest configuration for ticker-sentiment tests."""

import sys
from pathlib import Path

# Add the ticker-sentiment directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
