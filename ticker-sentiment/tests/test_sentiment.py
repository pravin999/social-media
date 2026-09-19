"""Tests for sentiment analysis functionality."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sentiment import SentimentAnalyzer


class TestSentimentAnalyzer:
    """Test the SentimentAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = SentimentAnalyzer()
    
    def test_analyze_post_positive(self):
        """Test analysis of a positive post."""
        text = "This stock is amazing! Great earnings and strong growth! 🚀"
        scores = self.analyzer.analyze_post(text)
        
        assert 'compound' in scores
        assert 'pos' in scores
        assert 'neu' in scores
        assert 'neg' in scores
        assert scores['compound'] > 0.05  # Should be positive
    
    def test_analyze_post_negative(self):
        """Test analysis of a negative post."""
        text = "This company is terrible. Awful management and declining profits."
        scores = self.analyzer.analyze_post(text)
        
        assert scores['compound'] < -0.05  # Should be negative
    
    def test_analyze_post_neutral(self):
        """Test analysis of a neutral post."""
        text = "The stock is at $150 today."
        scores = self.analyzer.analyze_post(text)
        
        assert -0.05 <= scores['compound'] <= 0.05  # Should be neutral
    
    def test_classify_sentiment_bullish(self):
        """Test bullish classification."""
        assert self.analyzer.classify_sentiment(0.6) == 'bullish'
        assert self.analyzer.classify_sentiment(0.05) == 'bullish'
    
    def test_classify_sentiment_bearish(self):
        """Test bearish classification."""
        assert self.analyzer.classify_sentiment(-0.6) == 'bearish'
        assert self.analyzer.classify_sentiment(-0.05) == 'bearish'
    
    def test_classify_sentiment_neutral(self):
        """Test neutral classification."""
        assert self.analyzer.classify_sentiment(0.0) == 'neutral'
        assert self.analyzer.classify_sentiment(0.04) == 'neutral'
        assert self.analyzer.classify_sentiment(-0.04) == 'neutral'
    
    def test_analyze_posts_empty(self):
        """Test analysis with no posts."""
        result = self.analyzer.analyze_posts([])
        
        assert result['total_posts'] == 0
        assert result['average_sentiment'] == 0.0
        assert result['sentiment_distribution'] == {'bullish': 0, 'neutral': 0, 'bearish': 0}
        assert result['top_bullish'] == []
        assert result['top_bearish'] == []
    
    def test_analyze_posts_mixed(self):
        """Test analysis with mixed sentiment posts."""
        posts = [
            {'text': 'This stock is amazing! Great earnings! 🚀', 'id': '1'},
            {'text': 'Terrible company, avoid at all costs', 'id': '2'},
            {'text': 'Stock price is $100', 'id': '3'},
            {'text': 'Love this company! Strong buy!', 'id': '4'},
            {'text': 'Disaster! Selling all my shares', 'id': '5'},
        ]
        
        result = self.analyzer.analyze_posts(posts)
        
        assert result['total_posts'] == 5
        assert -1.0 <= result['average_sentiment'] <= 1.0
        
        # Check distribution sums to total
        dist = result['sentiment_distribution']
        assert dist['bullish'] + dist['neutral'] + dist['bearish'] == 5
        
        # Check percentages sum to 100
        pct = result['sentiment_percentages']
        assert abs(pct['bullish'] + pct['neutral'] + pct['bearish'] - 100.0) < 0.01
        
        # Check we have top posts
        assert len(result['top_bullish']) > 0
        assert len(result['top_bearish']) > 0
        
        # Check posts are sorted correctly
        if len(result['top_bullish']) > 1:
            for i in range(len(result['top_bullish']) - 1):
                assert (result['top_bullish'][i]['sentiment_scores']['compound'] >= 
                       result['top_bullish'][i+1]['sentiment_scores']['compound'])
    
    def test_analyze_posts_all_bullish(self):
        """Test analysis with all bullish posts."""
        posts = [
            {'text': 'Amazing company! 🚀', 'id': '1'},
            {'text': 'Great earnings! Very bullish!', 'id': '2'},
            {'text': 'Love this stock!', 'id': '3'},
        ]
        
        result = self.analyzer.analyze_posts(posts)
        
        assert result['total_posts'] == 3
        assert result['average_sentiment'] > 0.05
        assert result['sentiment_distribution']['bullish'] == 3
    
    def test_analyze_posts_preserves_metadata(self):
        """Test that post metadata is preserved."""
        posts = [
            {
                'text': 'Great stock!',
                'id': '123',
                'url': 'https://twitter.com/i/web/status/123',
                'username': 'testuser',
                'created_at': '2024-01-01T00:00:00Z'
            }
        ]
        
        result = self.analyzer.analyze_posts(posts)
        
        analyzed = result['analyzed_posts'][0]
        assert analyzed['id'] == '123'
        assert analyzed['url'] == 'https://twitter.com/i/web/status/123'
        assert analyzed['username'] == 'testuser'
        assert analyzed['created_at'] == '2024-01-01T00:00:00Z'
        assert 'sentiment_scores' in analyzed
        assert 'sentiment_class' in analyzed
