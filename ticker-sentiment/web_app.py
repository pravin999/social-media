"""Optional web interface for ticker sentiment analysis."""

from flask import Flask, render_template, request, jsonify
from config import Config
from twitter_api import TwitterAPI
from sentiment import SentimentAnalyzer
import json

app = Flask(__name__)


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze sentiment for a ticker."""
    try:
        data = request.get_json()
        ticker = data.get('ticker', '').strip()
        
        if not ticker:
            return jsonify({'error': 'Ticker is required'}), 400
        
        hours = int(data.get('hours', Config.DEFAULT_LOOKBACK_HOURS))
        max_results = int(data.get('max_results', Config.DEFAULT_MAX_RESULTS))
        company_name = data.get('company_name', '').strip() or None
        
        # Validate configuration
        Config.validate()
        
        # Fetch and analyze
        twitter_api = TwitterAPI()
        sentiment_analyzer = SentimentAnalyzer()
        
        posts = twitter_api.search_recent_posts(
            ticker=ticker,
            lookback_hours=hours,
            max_results=max_results,
            include_company_name=company_name
        )
        
        if not posts:
            return jsonify({
                'ticker': ticker.upper(),
                'total_posts': 0,
                'message': f'No posts found for ${ticker.upper()} in the last {hours} hours.'
            })
        
        analysis = sentiment_analyzer.analyze_posts(posts)
        
        # Format response
        response = {
            'ticker': ticker.upper(),
            'total_posts': analysis['total_posts'],
            'average_sentiment': analysis['average_sentiment'],
            'sentiment_class': 'bullish' if analysis['average_sentiment'] >= 0.05 
                              else 'bearish' if analysis['average_sentiment'] <= -0.05 
                              else 'neutral',
            'distribution': analysis['sentiment_distribution'],
            'percentages': analysis['sentiment_percentages'],
            'top_bullish': [
                {
                    'text': p['text'],
                    'score': p['sentiment_scores']['compound'],
                    'url': p['url'],
                    'username': p.get('username', 'unknown')
                }
                for p in analysis['top_bullish'][:3]
            ],
            'top_bearish': [
                {
                    'text': p['text'],
                    'score': p['sentiment_scores']['compound'],
                    'url': p['url'],
                    'username': p.get('username', 'unknown')
                }
                for p in analysis['top_bearish'][:3]
            ]
        }
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


def run_web_app(host='127.0.0.1', port=5000, debug=False):
    """Run the web application.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_web_app(debug=True)
