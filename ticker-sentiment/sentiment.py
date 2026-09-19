"""Sentiment analysis using VADER."""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Dict, Tuple
from statistics import mean


class SentimentAnalyzer:
    """Analyze sentiment of social media posts."""
    
    def __init__(self):
        """Initialize the VADER sentiment analyzer."""
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze_post(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of a single post.
        
        Args:
            text: Post text to analyze
            
        Returns:
            Dictionary with sentiment scores:
            - compound: Overall sentiment (-1 to 1)
            - pos: Positive score (0 to 1)
            - neu: Neutral score (0 to 1)
            - neg: Negative score (0 to 1)
        """
        return self.analyzer.polarity_scores(text)
    
    def classify_sentiment(self, compound_score: float) -> str:
        """Classify sentiment based on compound score.
        
        Args:
            compound_score: VADER compound score (-1 to 1)
            
        Returns:
            'bullish', 'bearish', or 'neutral'
        """
        if compound_score >= 0.05:
            return 'bullish'
        elif compound_score <= -0.05:
            return 'bearish'
        else:
            return 'neutral'
    
    def analyze_posts(self, posts: List[Dict]) -> Dict:
        """Analyze sentiment across multiple posts.
        
        Args:
            posts: List of post dictionaries with 'text' key
            
        Returns:
            Dictionary with aggregated sentiment analysis:
            - total_posts: Number of posts analyzed
            - average_sentiment: Mean compound score
            - sentiment_distribution: Counts of bullish/neutral/bearish
            - sentiment_percentages: Percentage breakdown
            - top_bullish: List of most bullish posts
            - top_bearish: List of most bearish posts
            - analyzed_posts: All posts with sentiment scores
        """
        if not posts:
            return {
                'total_posts': 0,
                'average_sentiment': 0.0,
                'sentiment_distribution': {'bullish': 0, 'neutral': 0, 'bearish': 0},
                'sentiment_percentages': {'bullish': 0.0, 'neutral': 0.0, 'bearish': 0.0},
                'top_bullish': [],
                'top_bearish': [],
                'analyzed_posts': []
            }
        
        # Analyze each post
        analyzed_posts = []
        sentiment_counts = {'bullish': 0, 'neutral': 0, 'bearish': 0}
        
        for post in posts:
            scores = self.analyze_post(post['text'])
            sentiment_class = self.classify_sentiment(scores['compound'])
            
            analyzed_post = {
                **post,
                'sentiment_scores': scores,
                'sentiment_class': sentiment_class
            }
            analyzed_posts.append(analyzed_post)
            sentiment_counts[sentiment_class] += 1
        
        # Calculate aggregates
        compound_scores = [p['sentiment_scores']['compound'] for p in analyzed_posts]
        average_sentiment = mean(compound_scores)
        
        total_posts = len(analyzed_posts)
        sentiment_percentages = {
            sentiment: (count / total_posts * 100) if total_posts > 0 else 0.0
            for sentiment, count in sentiment_counts.items()
        }
        
        # Get top bullish and bearish posts
        sorted_by_sentiment = sorted(
            analyzed_posts,
            key=lambda x: x['sentiment_scores']['compound'],
            reverse=True
        )
        
        top_bullish = sorted_by_sentiment[:5]
        top_bearish = sorted_by_sentiment[-5:][::-1]  # Reverse to get most bearish first
        
        return {
            'total_posts': total_posts,
            'average_sentiment': average_sentiment,
            'sentiment_distribution': sentiment_counts,
            'sentiment_percentages': sentiment_percentages,
            'top_bullish': top_bullish,
            'top_bearish': top_bearish,
            'analyzed_posts': analyzed_posts
        }
