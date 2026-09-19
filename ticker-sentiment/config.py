"""Configuration management for the sentiment analysis tool."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration."""
    
    X_BEARER_TOKEN = os.getenv('X_BEARER_TOKEN')
    X_API_BASE_URL = 'https://api.twitter.com/2'
    
    # Default search parameters
    DEFAULT_LOOKBACK_HOURS = 24
    MAX_RESULTS_PER_REQUEST = 100  # X API v2 limit
    DEFAULT_MAX_RESULTS = 100
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.X_BEARER_TOKEN:
            raise ValueError(
                "X_BEARER_TOKEN not found. "
                "Please set it in your .env file or environment variables. "
                "See .env.example for setup instructions."
            )
        
        if cls.X_BEARER_TOKEN == 'your_bearer_token_here':
            raise ValueError(
                "Please replace the placeholder in .env with your actual X Bearer Token. "
                "Get one from: https://developer.twitter.com/en/portal/dashboard"
            )
