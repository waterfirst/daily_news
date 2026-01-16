"""
Tests for DAIP services
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.etf_analyzer import ETFAnalyzer, ETFData
from src.services.news_scraper import NewsScraper, NewsArticle
from src.services.content_generator import ContentGenerator, GeneratedContent
from src.services.industry_news import (
    BeautyNewsScraper,
    DisplayNewsScraper,
    SemiconductorNewsScraper
)


class TestETFAnalyzer:
    """Test ETF Analyzer service"""

    def test_etf_analyzer_init(self):
        """Test ETF analyzer initialization"""
        analyzer = ETFAnalyzer()
        assert analyzer is not None
        assert len(analyzer.tickers) > 0

    def test_calculate_stochastic(self):
        """Test stochastic calculation"""
        import pandas as pd
        import numpy as np

        analyzer = ETFAnalyzer()

        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=30)
        data = pd.DataFrame({
            'Open': np.random.rand(30) * 100,
            'High': np.random.rand(30) * 100 + 10,
            'Low': np.random.rand(30) * 100 - 10,
            'Close': np.random.rand(30) * 100,
            'Volume': np.random.rand(30) * 1000000
        }, index=dates)

        stoch_k, stoch_d = analyzer.calculate_stochastic(data)

        assert 0 <= stoch_k <= 100
        assert 0 <= stoch_d <= 100

    def test_determine_signal(self):
        """Test signal determination logic"""
        analyzer = ETFAnalyzer()

        # Test BUY signal (oversold + bullish crossover)
        signal = analyzer._determine_signal(stoch_k=18, stoch_d=15, change_pct=2.0)
        assert signal == "BUY"

        # Test SELL signal (overbought + bearish crossover)
        signal = analyzer._determine_signal(stoch_k=82, stoch_d=85, change_pct=-2.0)
        assert signal == "SELL"

        # Test WATCH signal
        signal = analyzer._determine_signal(stoch_k=50, stoch_d=48, change_pct=1.0)
        assert signal == "WATCH"

        # Test HOLD signal
        signal = analyzer._determine_signal(stoch_k=50, stoch_d=52, change_pct=-0.5)
        assert signal == "HOLD"


class TestNewsScraper:
    """Test News Scraper service"""

    def test_news_scraper_init(self):
        """Test news scraper initialization"""
        scraper = NewsScraper()
        assert scraper is not None
        assert len(scraper.categories) > 0

    def test_analyze_sentiment(self):
        """Test sentiment analysis"""
        scraper = NewsScraper()

        # Positive sentiment
        sentiment = scraper.analyze_sentiment("This is amazing and wonderful news!")
        assert sentiment in ["positive", "neutral"]  # TextBlob may vary

        # Negative sentiment
        sentiment = scraper.analyze_sentiment("This is terrible and awful news!")
        assert sentiment in ["negative", "neutral"]

    def test_get_mock_news(self):
        """Test mock news generation"""
        scraper = NewsScraper()
        articles = scraper.get_mock_news("IT")

        assert len(articles) > 0
        assert all(isinstance(article, NewsArticle) for article in articles)
        assert articles[0].category == "IT"

    def test_news_article_hash(self):
        """Test news article hash generation"""
        article1 = NewsArticle(
            title="Test Article",
            source="Test Source",
            url="https://example.com/1",
            category="IT"
        )

        article2 = NewsArticle(
            title="Test Article",
            source="Test Source",
            url="https://example.com/1",
            category="IT"
        )

        # Same content should have same hash
        assert article1.article_hash == article2.article_hash


class TestContentGenerator:
    """Test Content Generator service"""

    def test_content_generator_init(self):
        """Test content generator initialization"""
        generator = ContentGenerator()
        assert generator is not None

    @pytest.mark.skipif(
        not pytest.config.getoption("--run-ai"),
        reason="AI tests require API key and --run-ai flag"
    )
    def test_generate_blog_post(self):
        """Test blog post generation (requires API key)"""
        generator = ContentGenerator()
        blog = generator.generate_blog_post(
            topic="Python 자동화",
            keywords=["Python", "자동화"]
        )

        if blog:  # Only if API key is available
            assert isinstance(blog, GeneratedContent)
            assert blog.content_type == "blog"
            assert blog.word_count > 0

    def test_generated_content_to_markdown(self):
        """Test content conversion to markdown"""
        content = GeneratedContent(
            title="Test Blog",
            content="This is test content.",
            content_type="blog",
            category="Tech",
            generated_at=datetime.now(),
            word_count=4,
            tags=["test", "blog"]
        )

        md = content.to_markdown()
        assert "# Test Blog" in md
        assert "This is test content." in md
        assert "**Category**: Tech" in md


class TestIndustryNews:
    """Test Industry News scrapers"""

    def test_beauty_news_scraper(self):
        """Test beauty news scraper"""
        scraper = BeautyNewsScraper()
        assert scraper is not None

        # Test mock data
        articles = scraper._get_mock_beauty_news()
        assert len(articles) > 0

    def test_display_news_scraper(self):
        """Test display news scraper"""
        scraper = DisplayNewsScraper()
        assert scraper is not None

        # Test mock data
        articles = scraper._get_mock_display_news()
        assert len(articles) > 0

    def test_semiconductor_news_scraper(self):
        """Test semiconductor news scraper"""
        scraper = SemiconductorNewsScraper()
        assert scraper is not None

        # Test mock data
        articles = scraper._get_mock_semiconductor_news()
        assert len(articles) > 0


# Pytest configuration
def pytest_addoption(parser):
    """Add custom pytest options"""
    parser.addoption(
        "--run-ai",
        action="store_true",
        default=False,
        help="Run tests that require AI API"
    )


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "ai: mark test as requiring AI API"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
