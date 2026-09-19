# Ticker Sentiment Analysis

A reusable system for analyzing X (Twitter) sentiment on ANY stock or crypto ticker. Get real-time sentiment reports from recent posts about any ticker symbol.

## Features

- **Universal ticker support**: Works with any stock or crypto ticker (TSLA, AAPL, BTC, etc.)
- **X API v2 integration**: Fetches recent posts using official Twitter API
- **VADER sentiment analysis**: Accurate sentiment scoring with bullish/neutral/bearish classification
- **Flexible output**: Terminal reports (human-readable or JSON) and optional web UI
- **Configurable lookback**: Analyze posts from the last N hours
- **Sample top posts**: View the most bullish and bearish posts with links
- **Tested**: Comprehensive unit tests with mocked API responses

## Quick Start

### 1. Installation

```bash
cd ticker-sentiment
pip install -r requirements.txt
```

### 2. Get Your X API Token

1. Go to the [X Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new project and app (or use an existing one)
3. Navigate to your app's "Keys and tokens" section
4. Generate a **Bearer Token** (you'll need Essential access or higher)
5. Copy the token

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and paste your Bearer Token
# Replace 'your_bearer_token_here' with your actual token
```

Your `.env` file should look like:
```
X_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAALongStringOfCharacters
```

### 4. Run Analysis

#### CLI Usage

```bash
# Basic analysis
python3 -m ticker-sentiment TSLA

# Analyze different ticker with custom time window
python3 -m ticker-sentiment AAPL --hours 48

# Get JSON output for programmatic use
python3 -m ticker-sentiment BTC --json

# Increase results and include company name
python3 -m ticker-sentiment TSLA --max-results 200 --company-name "Tesla"

# Crypto analysis
python3 -m ticker-sentiment ETH --hours 12
```

#### Web UI (Optional)

```bash
# Start the web server
python3 web_app.py

# Open http://127.0.0.1:5000 in your browser
```

## Example Output

### Terminal Report

```
======================================================================
X (TWITTER) SENTIMENT ANALYSIS: $TSLA
======================================================================
Analysis Time: 2024-01-15 14:30:00 UTC
Lookback Period: 24 hours

SUMMARY
----------------------------------------------------------------------
Total Posts Analyzed: 87
Average Sentiment: BULLISH (0.245)

SENTIMENT DISTRIBUTION
----------------------------------------------------------------------
  🟢 Bullish:    52 posts ( 59.8%)
  ⚪ Neutral:    20 posts ( 23.0%)
  🔴 Bearish:    15 posts ( 17.2%)

TOP BULLISH POSTS
----------------------------------------------------------------------
1. Score: 0.891 | @tesla_investor
   Tesla's Q4 deliveries beat expectations! Strong demand continues...
   https://twitter.com/i/web/status/1234567890

2. Score: 0.856 | @ev_enthusiast
   Best EV company hands down. Innovation at its finest! 🚀...
   https://twitter.com/i/web/status/1234567891

TOP BEARISH POSTS
----------------------------------------------------------------------
1. Score: -0.782 | @market_bear
   Terrible valuation, avoid this stock at these levels...
   https://twitter.com/i/web/status/1234567892
```

### JSON Output

```bash
python3 -m ticker-sentiment TSLA --json > tsla_sentiment.json
```

```json
{
  "ticker": "TSLA",
  "analysis_time": "2024-01-15T14:30:00Z",
  "lookback_hours": 24,
  "summary": {
    "total_posts": 87,
    "average_sentiment": 0.245,
    "sentiment_classification": "bullish"
  },
  "distribution": {
    "counts": {
      "bullish": 52,
      "neutral": 20,
      "bearish": 15
    },
    "percentages": {
      "bullish": 59.8,
      "neutral": 23.0,
      "bearish": 17.2
    }
  },
  "top_bullish_posts": [...],
  "top_bearish_posts": [...]
}
```

## Command Line Options

```
python3 -m ticker-sentiment TICKER [OPTIONS]

Arguments:
  TICKER              Stock or crypto ticker symbol (e.g., TSLA, AAPL, BTC)

Options:
  --hours N           Hours to look back (default: 24)
  --max-results N     Maximum posts to fetch (default: 100, max: 100)
  --company-name NAME Optional company name to include in search
  --json              Output as JSON instead of human-readable format
  -h, --help          Show help message
```

## Use Cases

### 1. Quick Sentiment Check
```bash
python3 -m ticker-sentiment TSLA
```

### 2. Compare Multiple Tickers
```bash
for ticker in TSLA AAPL NVDA MSFT; do
  echo "=== $ticker ==="
  python3 -m ticker-sentiment $ticker --json
  echo ""
done
```

### 3. Extended Time Window
```bash
# Check weekend sentiment
python3 -m ticker-sentiment BTC --hours 72
```

### 4. Integration with Scripts
```python
import subprocess
import json

result = subprocess.run(
    ['python3', '-m', 'ticker-sentiment', 'AAPL', '--json'],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
print(f"Sentiment: {data['summary']['sentiment_classification']}")
```

## Running Tests

```bash
# Install test dependencies (if not already installed)
python3 -m pip install -r requirements.txt

# Run all tests
python3 -m pytest

# Run with coverage
python3 -m pytest --cov=ticker_sentiment

# Run specific test file
python3 -m pytest tests/test_sentiment.py

# Run verbose
python3 -m pytest -v
```

All tests use mocked X API responses, so no API token is needed for testing.

## Architecture

```
ticker-sentiment/
├── __init__.py           # Package initialization
├── __main__.py           # CLI entry point
├── config.py             # Configuration management
├── twitter_api.py        # X API v2 client
├── sentiment.py          # VADER sentiment analysis
├── report.py             # Report generation
├── web_app.py            # Optional Flask web UI
├── templates/
│   └── index.html        # Web UI template
├── tests/                # Unit tests with mocked responses
│   ├── test_sentiment.py
│   ├── test_twitter_api.py
│   └── test_report.py
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
└── README.md            # This file
```

## How It Works

1. **Query Building**: Constructs X API search query combining cashtag ($TSLA), ticker (TSLA), and optional company name
2. **Data Fetching**: Uses X API v2 `/tweets/search/recent` endpoint to fetch English posts excluding retweets
3. **Sentiment Analysis**: Applies VADER (Valence Aware Dictionary and sEntiment Reasoner) to score each post
4. **Classification**: Posts are classified as bullish (≥0.05), bearish (≤-0.05), or neutral
5. **Aggregation**: Calculates overall statistics, distribution, and identifies top posts
6. **Reporting**: Generates formatted output for terminal or JSON

## API Limitations

### X API v2 Free/Basic Tier

- **Rate limits**: 450 requests per 15 minutes (Basic tier)
- **Lookback**: Up to 7 days of historical data
- **Results**: Max 100 posts per request
- **Search operators**: Limited query complexity

### Recommendations

- Start with 24-hour windows to stay within rate limits
- Use `--max-results` to control data volume
- Add `--company-name` for better precision on common ticker symbols
- Monitor rate limit headers if running frequently

## Troubleshooting

### "X_BEARER_TOKEN not found"

Make sure you've created a `.env` file in the `ticker-sentiment/` directory with your token:

```bash
cd ticker-sentiment
cp .env.example .env
# Edit .env and add your token
```

### "Authentication failed"

- Verify your Bearer Token is correct (check for extra spaces)
- Ensure your X app has the correct access level
- Try regenerating your Bearer Token in the developer portal

### "No posts found"

- Some tickers may have low X volume
- Try increasing `--hours` to look back further
- Add `--company-name` to broaden the search
- Check if the ticker symbol is commonly discussed (e.g., $TSLA vs obscure penny stocks)

### "Rate limit exceeded"

- Wait 15 minutes before making more requests
- Reduce the frequency of your queries
- Consider caching results for frequently queried tickers

## Contributing

To extend this system:

1. **Add more sentiment engines**: Extend `sentiment.py` with TextBlob, Hugging Face models, etc.
2. **Support more sources**: Create new API clients similar to `twitter_api.py`
3. **Enhanced queries**: Modify `build_search_query()` to add filters (verified users, min engagement, etc.)
4. **Historical tracking**: Add database storage to track sentiment over time
5. **Visualization**: Create charts and graphs in the web UI

## License

This project is provided as-is for educational and personal use.

## Important Notes

- **Not Financial Advice**: This tool is for informational purposes only
- **API Costs**: Monitor your X API usage to avoid unexpected charges
- **Data Quality**: Social media sentiment can be noisy and manipulated
- **Compliance**: Ensure your use complies with X API Terms of Service

## Example Tickers

### Stocks
- **Tech**: AAPL, MSFT, GOOGL, AMZN, META, NVDA
- **EV/Auto**: TSLA, F, GM, RIVN
- **Finance**: JPM, GS, BAC, WFC
- **Meme Stocks**: GME, AMC

### Crypto
- **Major**: BTC, ETH, BNB
- **Alt**: SOL, ADA, DOGE, XRP
- **Meme**: SHIB, PEPE

---

**Built with**: Python, X API v2, VADER Sentiment, Flask

For issues or questions, please check the troubleshooting section or review the test files for usage examples.
