"""Setup script for ticker-sentiment package."""

from setuptools import setup, find_packages

setup(
    name='ticker-sentiment',
    version='1.0.0',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'requests>=2.31.0',
        'vaderSentiment>=3.3.2',
        'python-dotenv>=1.0.0',
        'Flask>=3.0.0',
    ],
    extras_require={
        'test': [
            'pytest>=7.4.0',
            'responses>=0.24.0',
        ]
    },
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'ticker-sentiment=ticker_sentiment.__main__:main',
        ],
    },
)
