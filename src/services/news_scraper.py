"""
News Scraping Service for Daily Automated Intelligence Platform (DAIP)
Scrapes and analyzes news from multiple sources
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import hashlib

from src.config import settings, NewsConfig
from src.logger import setup_logger
from src.telegram_bot import get_telegram_bot

logger = setup_logger("daip.news")


@dataclass
class NewsArticle:
    """News article data structure"""
    title: str
    source: str
    url: str
    category: str
    summary: Optional[str] = None
    sentiment: str = "neutral"  # positive, negative, neutral
    keywords: List[str] = None
    published_at: Optional[datetime] = None
    scraped_at: datetime = None
    article_hash: str = ""

    def __post_init__(self):
        """Post-initialization processing"""
        if self.scraped_at is None:
            self.scraped_at = datetime.now()
        if self.keywords is None:
            self.keywords = []
        if not self.article_hash:
            self.article_hash = self._generate_hash()

    def _generate_hash(self) -> str:
        """Generate unique hash for article"""
        content = f"{self.title}{self.url}"
        return hashlib.md5(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if self.published_at:
            data['published_at'] = self.published_at.isoformat()
        if self.scraped_at:
            data['scraped_at'] = self.scraped_at.isoformat()
        return data


class NewsScraper:
    """News scraping and analysis service"""

    def __init__(self):
        """Initialize news scraper"""
        self.categories = NewsConfig.CATEGORIES
        self.sources = NewsConfig.SOURCES
        self.top_n = NewsConfig.TOP_N_NEWS

        self.telegram_bot = get_telegram_bot()
        self.seen_articles = set()  # For duplicate detection

        logger.info("News Scraper initialized")

    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text

        Args:
            text: Text to analyze

        Returns:
            Sentiment (positive, negative, neutral)
        """
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity

            if polarity > 0.1:
                return "positive"
            elif polarity < -0.1:
                return "negative"
            else:
                return "neutral"
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return "neutral"

    def scrape_naver_news(self, category: str = "정치") -> List[NewsArticle]:
        """
        Scrape news from Naver

        Args:
            category: News category

        Returns:
            List of news articles
        """
        articles = []

        try:
            # Map Korean categories to Naver section codes
            category_map = {
                "정치": "100",
                "경제": "101",
                "사회": "102",
                "IT": "105",
                "AI": "105"
            }

            section_code = category_map.get(category, "100")
            url = f"https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1={section_code}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find news articles (this is a simplified example)
            news_items = soup.select('.cluster_text_headline')[:self.top_n]

            for item in news_items:
                try:
                    title_elem = item.select_one('a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')

                    # Create article
                    article = NewsArticle(
                        title=title,
                        source="Naver News",
                        url=link,
                        category=category,
                        sentiment=self.analyze_sentiment(title)
                    )

                    # Check for duplicates
                    if article.article_hash not in self.seen_articles:
                        articles.append(article)
                        self.seen_articles.add(article.article_hash)

                except Exception as e:
                    logger.error(f"Error parsing news item: {str(e)}")
                    continue

            logger.info(f"Scraped {len(articles)} articles from Naver ({category})")

        except Exception as e:
            logger.error(f"Error scraping Naver news: {str(e)}")

        return articles

    def scrape_google_news(self, query: str = "AI") -> List[NewsArticle]:
        """
        Scrape news from Google News

        Args:
            query: Search query

        Returns:
            List of news articles
        """
        articles = []

        try:
            url = f"https://news.google.com/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find articles (simplified)
            news_items = soup.select('article')[:self.top_n]

            for item in news_items:
                try:
                    title_elem = item.select_one('h3 a, h4 a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = "https://news.google.com" + title_elem.get('href', '').replace('.', '', 1)

                    article = NewsArticle(
                        title=title,
                        source="Google News",
                        url=link,
                        category=query,
                        sentiment=self.analyze_sentiment(title)
                    )

                    if article.article_hash not in self.seen_articles:
                        articles.append(article)
                        self.seen_articles.add(article.article_hash)

                except Exception as e:
                    logger.error(f"Error parsing Google news item: {str(e)}")
                    continue

            logger.info(f"Scraped {len(articles)} articles from Google News ({query})")

        except Exception as e:
            logger.error(f"Error scraping Google news: {str(e)}")

        return articles

    def get_mock_news(self, category: str = "종합") -> List[NewsArticle]:
        """
        Generate mock news for testing

        Args:
            category: News category

        Returns:
            List of mock news articles
        """
        mock_articles = [
            NewsArticle(
                title=f"{category} 분야 AI 기술 발전으로 산업 혁신 가속화",
                source="Mock News Source",
                url="https://example.com/news1",
                category=category,
                sentiment="positive"
            ),
            NewsArticle(
                title=f"{category} 시장 성장세 지속, 전문가들 긍정 전망",
                source="Mock News Source",
                url="https://example.com/news2",
                category=category,
                sentiment="positive"
            ),
            NewsArticle(
                title=f"{category} 규제 강화 우려, 업계 대응 방안 모색",
                source="Mock News Source",
                url="https://example.com/news3",
                category=category,
                sentiment="negative"
            ),
            NewsArticle(
                title=f"{category} 신기술 개발 경쟁 심화, 투자 증가 추세",
                source="Mock News Source",
                url="https://example.com/news4",
                category=category,
                sentiment="neutral"
            ),
            NewsArticle(
                title=f"{category} 글로벌 협력 확대, 한국 기업 진출 활발",
                source="Mock News Source",
                url="https://example.com/news5",
                category=category,
                sentiment="positive"
            ),
        ]

        logger.info(f"Generated {len(mock_articles)} mock articles for {category}")
        return mock_articles

    def scrape_all_categories(self, use_mock: bool = False) -> Dict[str, List[NewsArticle]]:
        """
        Scrape news from all categories

        Args:
            use_mock: Use mock data for testing

        Returns:
            Dictionary mapping category to list of articles
        """
        all_news = {}

        for category in self.categories:
            logger.info(f"Scraping news for category: {category}")

            if use_mock:
                articles = self.get_mock_news(category)
            else:
                # Try Naver first, fallback to Google
                articles = self.scrape_naver_news(category)

                if not articles:
                    logger.warning(f"No articles from Naver for {category}, trying Google")
                    articles = self.scrape_google_news(category)

            all_news[category] = articles

        return all_news

    def run(self, use_mock: bool = False) -> bool:
        """
        Run news scraping and send report

        Args:
            use_mock: Use mock data for testing

        Returns:
            True if successful
        """
        try:
            logger.info("Starting news scraping run")

            # Scrape all categories
            all_news = self.scrape_all_categories(use_mock=use_mock)

            if not all_news:
                logger.warning("No news articles scraped")
                return False

            # Send reports for each category
            success_count = 0
            for category, articles in all_news.items():
                if articles:
                    news_data = [
                        {
                            'title': article.title,
                            'source': article.source,
                            'url': article.url,
                            'sentiment': article.sentiment
                        }
                        for article in articles[:self.top_n]
                    ]

                    if self.telegram_bot.send_news_report(news_data, category):
                        success_count += 1

            logger.info(f"Sent {success_count}/{len(all_news)} news reports")
            return success_count > 0

        except Exception as e:
            logger.error(f"News scraping run failed: {str(e)}")
            self.telegram_bot.send_error_notification(
                "News Scraper",
                str(e)
            )
            return False


# Service instance
_news_scraper: Optional[NewsScraper] = None


def get_news_scraper() -> NewsScraper:
    """Get or create news scraper instance"""
    global _news_scraper
    if _news_scraper is None:
        _news_scraper = NewsScraper()
    return _news_scraper


def run_news_scraping(use_mock: bool = False) -> None:
    """Run news scraping (for scheduler)"""
    scraper = get_news_scraper()
    scraper.run(use_mock=use_mock)


# Example usage
if __name__ == "__main__":
    # Test news scraper
    scraper = NewsScraper()

    # Test with mock data
    scraper.run(use_mock=True)
