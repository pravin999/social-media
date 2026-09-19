"""Report generation for sentiment analysis results."""

import json
from typing import Dict
from datetime import datetime


class ReportGenerator:
    """Generate human-readable and JSON reports."""
    
    @staticmethod
    def format_sentiment_class(sentiment: float) -> str:
        """Format sentiment score with color indicators.
        
        Args:
            sentiment: Compound sentiment score
            
        Returns:
            Formatted sentiment string
        """
        if sentiment >= 0.05:
            return f"BULLISH ({sentiment:.3f})"
        elif sentiment <= -0.05:
            return f"BEARISH ({sentiment:.3f})"
        else:
            return f"NEUTRAL ({sentiment:.3f})"
    
    @staticmethod
    def generate_terminal_report(ticker: str, analysis: Dict, lookback_hours: int) -> str:
        """Generate a human-readable terminal report.
        
        Args:
            ticker: Stock/crypto ticker
            analysis: Analysis results from SentimentAnalyzer
            lookback_hours: Hours of data analyzed
            
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"X (TWITTER) SENTIMENT ANALYSIS: ${ticker.upper()}")
        lines.append("=" * 70)
        lines.append(f"Analysis Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"Lookback Period: {lookback_hours} hours")
        lines.append("")
        
        # Summary statistics
        lines.append("SUMMARY")
        lines.append("-" * 70)
        lines.append(f"Total Posts Analyzed: {analysis['total_posts']}")
        lines.append(f"Average Sentiment: {ReportGenerator.format_sentiment_class(analysis['average_sentiment'])}")
        lines.append("")
        
        # Distribution
        lines.append("SENTIMENT DISTRIBUTION")
        lines.append("-" * 70)
        dist = analysis['sentiment_distribution']
        pct = analysis['sentiment_percentages']
        lines.append(f"  🟢 Bullish:  {dist['bullish']:4d} posts ({pct['bullish']:5.1f}%)")
        lines.append(f"  ⚪ Neutral:  {dist['neutral']:4d} posts ({pct['neutral']:5.1f}%)")
        lines.append(f"  🔴 Bearish:  {dist['bearish']:4d} posts ({pct['bearish']:5.1f}%)")
        lines.append("")
        
        # Top bullish posts
        if analysis['top_bullish']:
            lines.append("TOP BULLISH POSTS")
            lines.append("-" * 70)
            for i, post in enumerate(analysis['top_bullish'][:3], 1):
                score = post['sentiment_scores']['compound']
                text = post['text'].replace('\n', ' ')[:100]
                username = post.get('username', 'unknown')
                lines.append(f"{i}. Score: {score:.3f} | @{username}")
                lines.append(f"   {text}...")
                lines.append(f"   {post['url']}")
                lines.append("")
        
        # Top bearish posts
        if analysis['top_bearish']:
            lines.append("TOP BEARISH POSTS")
            lines.append("-" * 70)
            for i, post in enumerate(analysis['top_bearish'][:3], 1):
                score = post['sentiment_scores']['compound']
                text = post['text'].replace('\n', ' ')[:100]
                username = post.get('username', 'unknown')
                lines.append(f"{i}. Score: {score:.3f} | @{username}")
                lines.append(f"   {text}...")
                lines.append(f"   {post['url']}")
                lines.append("")
        
        lines.append("=" * 70)
        lines.append("NOTE: Sentiment scores range from -1 (most bearish) to +1 (most bullish)")
        lines.append("      Analysis uses VADER sentiment analysis on English posts only")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_json_report(ticker: str, analysis: Dict, lookback_hours: int) -> str:
        """Generate a JSON report.
        
        Args:
            ticker: Stock/crypto ticker
            analysis: Analysis results from SentimentAnalyzer
            lookback_hours: Hours of data analyzed
            
        Returns:
            JSON string
        """
        report = {
            'ticker': ticker.upper(),
            'analysis_time': datetime.utcnow().isoformat() + 'Z',
            'lookback_hours': lookback_hours,
            'summary': {
                'total_posts': analysis['total_posts'],
                'average_sentiment': analysis['average_sentiment'],
                'sentiment_classification': 'bullish' if analysis['average_sentiment'] >= 0.05 
                                          else 'bearish' if analysis['average_sentiment'] <= -0.05 
                                          else 'neutral'
            },
            'distribution': {
                'counts': analysis['sentiment_distribution'],
                'percentages': analysis['sentiment_percentages']
            },
            'top_bullish_posts': [
                {
                    'text': p['text'],
                    'sentiment_score': p['sentiment_scores']['compound'],
                    'url': p['url'],
                    'username': p.get('username', 'unknown'),
                    'created_at': p.get('created_at', '')
                }
                for p in analysis['top_bullish'][:5]
            ],
            'top_bearish_posts': [
                {
                    'text': p['text'],
                    'sentiment_score': p['sentiment_scores']['compound'],
                    'url': p['url'],
                    'username': p.get('username', 'unknown'),
                    'created_at': p.get('created_at', '')
                }
                for p in analysis['top_bearish'][:5]
            ]
        }
        
        return json.dumps(report, indent=2)
