"""Tests for report generation."""

import json
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from report import ReportGenerator


class TestReportGenerator:
    """Test the ReportGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_analysis = {
            'total_posts': 50,
            'average_sentiment': 0.25,
            'sentiment_distribution': {
                'bullish': 30,
                'neutral': 10,
                'bearish': 10
            },
            'sentiment_percentages': {
                'bullish': 60.0,
                'neutral': 20.0,
                'bearish': 20.0
            },
            'top_bullish': [
                {
                    'text': 'Amazing stock! 🚀',
                    'sentiment_scores': {'compound': 0.85},
                    'url': 'https://twitter.com/i/web/status/123',
                    'username': 'bull_trader'
                },
                {
                    'text': 'Great earnings report!',
                    'sentiment_scores': {'compound': 0.75},
                    'url': 'https://twitter.com/i/web/status/124',
                    'username': 'investor_pro'
                }
            ],
            'top_bearish': [
                {
                    'text': 'Terrible company, avoid!',
                    'sentiment_scores': {'compound': -0.80},
                    'url': 'https://twitter.com/i/web/status/125',
                    'username': 'bear_trader'
                }
            ],
            'analyzed_posts': []
        }
    
    def test_format_sentiment_class_bullish(self):
        """Test formatting of bullish sentiment."""
        result = ReportGenerator.format_sentiment_class(0.5)
        assert 'BULLISH' in result
        assert '0.500' in result
    
    def test_format_sentiment_class_bearish(self):
        """Test formatting of bearish sentiment."""
        result = ReportGenerator.format_sentiment_class(-0.5)
        assert 'BEARISH' in result
        assert '-0.500' in result
    
    def test_format_sentiment_class_neutral(self):
        """Test formatting of neutral sentiment."""
        result = ReportGenerator.format_sentiment_class(0.0)
        assert 'NEUTRAL' in result
        assert '0.000' in result
    
    def test_generate_terminal_report(self):
        """Test terminal report generation."""
        report = ReportGenerator.generate_terminal_report(
            'TSLA', self.sample_analysis, 24
        )
        
        assert '$TSLA' in report
        assert 'Total Posts Analyzed: 50' in report
        assert 'BULLISH' in report
        assert '60.0%' in report
        assert '20.0%' in report
        assert 'Amazing stock!' in report
        assert 'Terrible company' in report
        assert 'https://twitter.com/i/web/status/123' in report
    
    def test_generate_terminal_report_empty(self):
        """Test terminal report with no data."""
        empty_analysis = {
            'total_posts': 0,
            'average_sentiment': 0.0,
            'sentiment_distribution': {'bullish': 0, 'neutral': 0, 'bearish': 0},
            'sentiment_percentages': {'bullish': 0.0, 'neutral': 0.0, 'bearish': 0.0},
            'top_bullish': [],
            'top_bearish': [],
            'analyzed_posts': []
        }
        
        report = ReportGenerator.generate_terminal_report(
            'UNKNOWN', empty_analysis, 24
        )
        
        assert '$UNKNOWN' in report
        assert 'Total Posts Analyzed: 0' in report
    
    def test_generate_json_report(self):
        """Test JSON report generation."""
        report_str = ReportGenerator.generate_json_report(
            'TSLA', self.sample_analysis, 24
        )
        
        report = json.loads(report_str)
        
        assert report['ticker'] == 'TSLA'
        assert report['lookback_hours'] == 24
        assert report['summary']['total_posts'] == 50
        assert report['summary']['average_sentiment'] == 0.25
        assert report['summary']['sentiment_classification'] == 'bullish'
        assert report['distribution']['counts']['bullish'] == 30
        assert report['distribution']['percentages']['bullish'] == 60.0
        assert len(report['top_bullish_posts']) == 2
        assert len(report['top_bearish_posts']) == 1
    
    def test_generate_json_report_structure(self):
        """Test JSON report has correct structure."""
        report_str = ReportGenerator.generate_json_report(
            'AAPL', self.sample_analysis, 48
        )
        
        report = json.loads(report_str)
        
        # Check required fields
        assert 'ticker' in report
        assert 'analysis_time' in report
        assert 'lookback_hours' in report
        assert 'summary' in report
        assert 'distribution' in report
        assert 'top_bullish_posts' in report
        assert 'top_bearish_posts' in report
        
        # Check summary fields
        assert 'total_posts' in report['summary']
        assert 'average_sentiment' in report['summary']
        assert 'sentiment_classification' in report['summary']
        
        # Check distribution fields
        assert 'counts' in report['distribution']
        assert 'percentages' in report['distribution']
    
    def test_generate_json_report_bearish_classification(self):
        """Test JSON report with bearish overall sentiment."""
        bearish_analysis = {
            **self.sample_analysis,
            'average_sentiment': -0.30
        }
        
        report_str = ReportGenerator.generate_json_report(
            'BEAR', bearish_analysis, 24
        )
        
        report = json.loads(report_str)
        assert report['summary']['sentiment_classification'] == 'bearish'
    
    def test_generate_json_report_neutral_classification(self):
        """Test JSON report with neutral overall sentiment."""
        neutral_analysis = {
            **self.sample_analysis,
            'average_sentiment': 0.02
        }
        
        report_str = ReportGenerator.generate_json_report(
            'NEUT', neutral_analysis, 24
        )
        
        report = json.loads(report_str)
        assert report['summary']['sentiment_classification'] == 'neutral'
