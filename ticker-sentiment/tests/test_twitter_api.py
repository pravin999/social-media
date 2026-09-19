"""Tests for X API integration."""

import pytest
import responses
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from twitter_api import TwitterAPI
from config import Config


class TestTwitterAPI:
    """Test the TwitterAPI class."""
    
    def test_build_search_query_basic(self):
        """Test basic query building."""
        api = TwitterAPI(bearer_token='test_token')
        query = api.build_search_query('TSLA')
        
        assert '$TSLA' in query
        assert 'TSLA' in query
        assert '-is:retweet' in query
        assert 'lang:en' in query
    
    def test_build_search_query_with_company_name(self):
        """Test query building with company name."""
        api = TwitterAPI(bearer_token='test_token')
        query = api.build_search_query('TSLA', include_company_name='Tesla')
        
        assert '$TSLA' in query
        assert 'TSLA' in query
        assert 'Tesla' in query
    
    def test_build_search_query_lowercase_ticker(self):
        """Test that lowercase tickers are converted to uppercase."""
        api = TwitterAPI(bearer_token='test_token')
        query = api.build_search_query('aapl')
        
        assert '$AAPL' in query
        assert 'AAPL' in query
    
    @responses.activate
    def test_search_recent_posts_success(self):
        """Test successful post search."""
        api = TwitterAPI(bearer_token='test_token')
        
        # Mock API response
        mock_response = {
            'data': [
                {
                    'id': '1234567890',
                    'text': 'Great stock! $TSLA to the moon!',
                    'created_at': '2024-01-01T12:00:00.000Z',
                    'author_id': 'user123',
                    'public_metrics': {
                        'like_count': 10,
                        'retweet_count': 5
                    }
                },
                {
                    'id': '9876543210',
                    'text': 'Not sure about TSLA anymore',
                    'created_at': '2024-01-01T11:00:00.000Z',
                    'author_id': 'user456',
                    'public_metrics': {
                        'like_count': 3,
                        'retweet_count': 1
                    }
                }
            ],
            'includes': {
                'users': [
                    {'id': 'user123', 'username': 'bullish_trader'},
                    {'id': 'user456', 'username': 'skeptical_investor'}
                ]
            }
        }
        
        responses.add(
            responses.GET,
            f'{Config.X_API_BASE_URL}/tweets/search/recent',
            json=mock_response,
            status=200
        )
        
        posts = api.search_recent_posts('TSLA', lookback_hours=24)
        
        assert len(posts) == 2
        assert posts[0]['id'] == '1234567890'
        assert posts[0]['text'] == 'Great stock! $TSLA to the moon!'
        assert posts[0]['username'] == 'bullish_trader'
        assert 'url' in posts[0]
        assert 'metrics' in posts[0]
    
    @responses.activate
    def test_search_recent_posts_no_results(self):
        """Test handling of no results."""
        api = TwitterAPI(bearer_token='test_token')
        
        responses.add(
            responses.GET,
            f'{Config.X_API_BASE_URL}/tweets/search/recent',
            json={'meta': {'result_count': 0}},
            status=200
        )
        
        posts = api.search_recent_posts('UNKNOWNSTOCK')
        
        assert posts == []
    
    @responses.activate
    def test_search_recent_posts_auth_error(self):
        """Test handling of authentication errors."""
        api = TwitterAPI(bearer_token='invalid_token')
        
        responses.add(
            responses.GET,
            f'{Config.X_API_BASE_URL}/tweets/search/recent',
            json={'errors': [{'message': 'Unauthorized'}]},
            status=401
        )
        
        with pytest.raises(ValueError, match='Authentication failed'):
            api.search_recent_posts('TSLA')
    
    @responses.activate
    def test_search_recent_posts_rate_limit(self):
        """Test handling of rate limit errors."""
        api = TwitterAPI(bearer_token='test_token')
        
        responses.add(
            responses.GET,
            f'{Config.X_API_BASE_URL}/tweets/search/recent',
            json={'errors': [{'message': 'Rate limit exceeded'}]},
            status=429
        )
        
        with pytest.raises(ValueError, match='Rate limit exceeded'):
            api.search_recent_posts('TSLA')
    
    @responses.activate
    def test_search_recent_posts_respects_max_results(self):
        """Test that max_results parameter is respected."""
        api = TwitterAPI(bearer_token='test_token')
        
        responses.add(
            responses.GET,
            f'{Config.X_API_BASE_URL}/tweets/search/recent',
            json={'data': []},
            status=200
        )
        
        api.search_recent_posts('TSLA', max_results=50)
        
        # Check the request was made with correct max_results
        assert len(responses.calls) == 1
        assert 'max_results=50' in responses.calls[0].request.url
    
    def test_get_headers(self):
        """Test authentication headers."""
        api = TwitterAPI(bearer_token='my_test_token')
        headers = api._get_headers()
        
        assert headers['Authorization'] == 'Bearer my_test_token'
        assert 'User-Agent' in headers
