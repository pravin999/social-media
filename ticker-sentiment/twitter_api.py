"""X API v2 integration for fetching posts."""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import Config


class TwitterAPI:
    """Client for X API v2 recent search."""
    
    def __init__(self, bearer_token: Optional[str] = None):
        """Initialize the X API client.
        
        Args:
            bearer_token: X API Bearer Token (defaults to Config.X_BEARER_TOKEN)
        """
        self.bearer_token = bearer_token or Config.X_BEARER_TOKEN
        self.base_url = Config.X_API_BASE_URL
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        return {
            'Authorization': f'Bearer {self.bearer_token}',
            'User-Agent': 'TickerSentimentAnalysis/1.0'
        }
    
    def build_search_query(self, ticker: str, include_company_name: Optional[str] = None) -> str:
        """Build search query for a ticker.
        
        Args:
            ticker: Stock/crypto ticker symbol (e.g., TSLA, BTC)
            include_company_name: Optional company name to include in search
            
        Returns:
            X API search query string
        """
        # Search for both cashtag ($TSLA) and plain ticker (TSLA)
        ticker_upper = ticker.upper()
        query_parts = [f'${ticker_upper}', ticker_upper]
        
        if include_company_name:
            query_parts.append(include_company_name)
        
        # Combine with OR, exclude retweets, require English
        query = f'({" OR ".join(query_parts)}) -is:retweet lang:en'
        
        return query
    
    def search_recent_posts(
        self,
        ticker: str,
        lookback_hours: int = Config.DEFAULT_LOOKBACK_HOURS,
        max_results: int = Config.DEFAULT_MAX_RESULTS,
        include_company_name: Optional[str] = None
    ) -> List[Dict]:
        """Search for recent posts about a ticker.
        
        Args:
            ticker: Stock/crypto ticker symbol
            lookback_hours: Hours to look back (default 24)
            max_results: Maximum number of results to fetch
            include_company_name: Optional company name to include in search
            
        Returns:
            List of post dictionaries with id, text, created_at, author_id
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        query = self.build_search_query(ticker, include_company_name)
        
        # Calculate start time
        start_time = datetime.utcnow() - timedelta(hours=lookback_hours)
        start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Build request parameters
        params = {
            'query': query,
            'max_results': min(max_results, Config.MAX_RESULTS_PER_REQUEST),
            'start_time': start_time_str,
            'tweet.fields': 'created_at,public_metrics,author_id',
            'expansions': 'author_id',
            'user.fields': 'username'
        }
        
        url = f'{self.base_url}/tweets/search/recent'
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle no results
            if 'data' not in data:
                return []
            
            # Extract user information for author mapping
            users = {}
            if 'includes' in data and 'users' in data['includes']:
                users = {user['id']: user for user in data['includes']['users']}
            
            # Format posts
            posts = []
            for tweet in data['data']:
                post = {
                    'id': tweet['id'],
                    'text': tweet['text'],
                    'created_at': tweet['created_at'],
                    'author_id': tweet.get('author_id'),
                    'url': f"https://twitter.com/i/web/status/{tweet['id']}"
                }
                
                # Add username if available
                if post['author_id'] in users:
                    post['username'] = users[post['author_id']].get('username')
                
                # Add engagement metrics
                if 'public_metrics' in tweet:
                    post['metrics'] = tweet['public_metrics']
                
                posts.append(post)
            
            return posts
            
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError(
                    "Authentication failed. Please check your X_BEARER_TOKEN. "
                    "Error: " + str(e)
                )
            elif e.response.status_code == 429:
                raise ValueError(
                    "Rate limit exceeded. Please wait before making more requests. "
                    "Error: " + str(e)
                )
            else:
                raise
