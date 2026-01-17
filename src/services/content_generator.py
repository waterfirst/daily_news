"""
AI Content Generation Service for Daily Automated Intelligence Platform (DAIP)
Generates blog posts, newsletters, and reports using Claude AI
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import anthropic
from pathlib import Path

from src.config import settings, ContentConfig
from src.logger import setup_logger
from src.telegram_bot import get_telegram_bot
from src.services.news_scraper import NewsArticle

logger = setup_logger("daip.content")


@dataclass
class GeneratedContent:
    """Generated content data structure"""
    title: str
    content: str
    content_type: str  # blog, newsletter, report, column
    category: str
    generated_at: datetime
    word_count: int
    summary: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.word_count:
            self.word_count = len(self.content.split())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        return data

    def to_markdown(self) -> str:
        """Convert to Markdown format"""
        md = f"# {self.title}\n\n"
        md += f"**Category**: {self.category}\n"
        md += f"**Type**: {self.content_type}\n"
        md += f"**Generated**: {self.generated_at.strftime('%Y-%m-%d %H:%M')}\n"
        md += f"**Words**: {self.word_count}\n\n"

        if self.tags:
            md += f"**Tags**: {', '.join(self.tags)}\n\n"

        md += "---\n\n"

        if self.summary:
            md += f"## Summary\n\n{self.summary}\n\n"

        md += f"{self.content}\n"

        return md


class ContentGenerator:
    """AI-powered content generation service"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize content generator

        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.client = None
        self.enabled = True

        if not self.api_key or not self.api_key.strip():
            logger.warning("Anthropic API key not configured - content generation will be disabled")
            self.enabled = False
        else:
            try:
                self.client = anthropic.Client(api_key=self.api_key)
                logger.info("Claude API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Claude API client: {str(e)}")
                self.enabled = False

        self.telegram_bot = get_telegram_bot()
        self.output_dir = Path(ContentConfig.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Content Generator initialized")

    def generate_with_claude(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate content using Claude API

        Args:
            prompt: Generation prompt
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature (0-1)

        Returns:
            Generated text
        """
        if not self.client:
            logger.error("Claude API client not initialized")
            return ""

        try:
            logger.info("Generating content with Claude")

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
            logger.info(f"Generated {len(content)} characters")
            return content

        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return ""

    def generate_blog_post(
        self,
        topic: str,
        context: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> Optional[GeneratedContent]:
        """
        Generate a blog post

        Args:
            topic: Blog post topic
            context: Additional context or data
            keywords: SEO keywords

        Returns:
            GeneratedContent object
        """
        logger.info(f"Generating blog post: {topic}")

        # Create prompt
        prompt = f"""당신은 전문 기술 블로거입니다. 다음 주제로 흥미롭고 유익한 블로그 포스트를 작성해주세요.

주제: {topic}

요구사항:
1. 2000-3000 단어 분량
2. 명확한 구조 (도입, 본문, 결론)
3. 실용적인 예시와 인사이트 포함
4. 독자 친화적이고 이해하기 쉬운 문체
5. SEO를 고려한 제목과 소제목
"""

        if context:
            prompt += f"\n\n참고 자료:\n{context}\n"

        if keywords:
            prompt += f"\n\nSEO 키워드: {', '.join(keywords)}\n"

        prompt += "\n\n블로그 포스트를 Markdown 형식으로 작성해주세요."

        # Generate content
        content = self.generate_with_claude(prompt, max_tokens=4000)

        if not content:
            return None

        # Extract title (first h1)
        lines = content.split('\n')
        title = topic
        for line in lines:
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                break

        # Create summary
        summary = content.split('\n\n')[0][:200] + "..."

        return GeneratedContent(
            title=title,
            content=content,
            content_type="blog",
            category=topic,
            generated_at=datetime.now(),
            word_count=len(content.split()),
            summary=summary,
            tags=keywords or []
        )

    def generate_newsletter(
        self,
        news_items: List[NewsArticle],
        topic: str = "주간 뉴스"
    ) -> Optional[GeneratedContent]:
        """
        Generate newsletter from news articles

        Args:
            news_items: List of news articles
            topic: Newsletter topic

        Returns:
            GeneratedContent object
        """
        logger.info(f"Generating newsletter: {topic}")

        # Prepare news summary
        news_summary = "\n\n".join([
            f"- {article.title} ({article.source})"
            for article in news_items[:10]
        ])

        prompt = f"""당신은 전문 뉴스레터 작가입니다. 다음 뉴스 항목들을 바탕으로 매력적인 뉴스레터를 작성해주세요.

주제: {topic}

뉴스 항목:
{news_summary}

요구사항:
1. 도입부: 이번 주 주요 트렌드 요약
2. 본문: 각 뉴스에 대한 간단한 분석과 의미
3. 결론: 향후 전망 및 시사점
4. 읽기 쉬운 형식 (불릿 포인트, 섹션 구분)
5. 전문적이면서도 흥미로운 문체

뉴스레터를 Markdown 형식으로 작성해주세요.
"""

        content = self.generate_with_claude(prompt, max_tokens=3000)

        if not content:
            return None

        return GeneratedContent(
            title=f"{topic} - {datetime.now().strftime('%Y년 %m월 %d일')}",
            content=content,
            content_type="newsletter",
            category=topic,
            generated_at=datetime.now(),
            word_count=len(content.split()),
            tags=["newsletter", topic]
        )

    def generate_future_prediction(
        self,
        domain: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[GeneratedContent]:
        """
        Generate future prediction column

        Args:
            domain: Domain for prediction (AI, investment, technology)
            data: Supporting data

        Returns:
            GeneratedContent object
        """
        logger.info(f"Generating future prediction: {domain}")

        prompt = f"""당신은 미래 트렌드 분석 전문가입니다. {domain} 분야의 향후 3-5년 전망을 분석하는 칼럼을 작성해주세요.

요구사항:
1. 현재 상황 분석
2. 주요 변화 동인 (기술, 시장, 규제 등)
3. 시나리오별 전망 (낙관적, 중립적, 비관적)
4. 실무적 시사점
5. 데이터와 근거에 기반한 분석

칼럼 형식으로 작성해주세요 (1500-2000 단어).
"""

        if data:
            prompt += f"\n\n참고 데이터:\n{str(data)}\n"

        content = self.generate_with_claude(prompt, max_tokens=3500)

        if not content:
            return None

        return GeneratedContent(
            title=f"{domain} 미래 전망 - {datetime.now().year}년",
            content=content,
            content_type="column",
            category=domain,
            generated_at=datetime.now(),
            word_count=len(content.split()),
            tags=["future", "prediction", domain]
        )

    def generate_technical_report(
        self,
        topic: str,
        data: Dict[str, Any]
    ) -> Optional[GeneratedContent]:
        """
        Generate technical analysis report

        Args:
            topic: Report topic
            data: Analysis data

        Returns:
            GeneratedContent object
        """
        logger.info(f"Generating technical report: {topic}")

        prompt = f"""당신은 기술 분석 전문가입니다. 다음 데이터를 분석하여 상세한 기술 리포트를 작성해주세요.

주제: {topic}

데이터:
{str(data)}

요구사항:
1. Executive Summary
2. 데이터 분석 (트렌드, 패턴, 이상치)
3. 주요 발견사항
4. 권장사항
5. 결론

리포트 형식으로 작성해주세요.
"""

        content = self.generate_with_claude(prompt, max_tokens=4000)

        if not content:
            return None

        return GeneratedContent(
            title=f"{topic} 기술 분석 리포트",
            content=content,
            content_type="report",
            category=topic,
            generated_at=datetime.now(),
            word_count=len(content.split()),
            tags=["technical", "analysis", topic]
        )

    def save_content(self, content: GeneratedContent, format: str = "md") -> Path:
        """
        Save generated content to file

        Args:
            content: GeneratedContent object
            format: Output format (md, txt, html)

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{content.content_type}_{timestamp}.{format}"
        filepath = self.output_dir / filename

        try:
            if format == "md":
                text = content.to_markdown()
            else:
                text = content.content

            filepath.write_text(text, encoding='utf-8')
            logger.info(f"Content saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving content: {str(e)}")
            return None

    def run_daily_content_generation(self) -> bool:
        """
        Run daily content generation

        Returns:
            True if successful
        """
        try:
            logger.info("Starting daily content generation")

            if not self.enabled:
                logger.warning("Content generation is disabled - API key not configured")
                logger.info("Content generation service completed (skipped - no API key)")
                return True

            # Generate blog post
            blog = self.generate_blog_post(
                topic="AI와 자동화가 바꾸는 미래",
                keywords=["AI", "자동화", "미래", "기술"]
            )

            if blog:
                self.save_content(blog)
                logger.info(f"Blog post generated: {blog.title}")

            # Generate future prediction
            prediction = self.generate_future_prediction(
                domain="AI 기술",
            )

            if prediction:
                self.save_content(prediction)
                logger.info(f"Prediction generated: {prediction.title}")

            # Send notification (but don't fail if telegram fails)
            try:
                message = "📝 <b>일일 콘텐츠 생성 완료</b>\n\n"
                if blog:
                    message += f"✅ Blog: {blog.title}\n"
                if prediction:
                    message += f"✅ Column: {prediction.title}\n"

                message += f"\n🕐 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                telegram_success = self.telegram_bot.send_message(message)
                if telegram_success:
                    logger.info("Content generation notification sent via Telegram")
                else:
                    logger.warning("Could not send notification via Telegram")
            except Exception as notify_error:
                logger.error(f"Failed to send Telegram notification: {str(notify_error)}")

            logger.info("Daily content generation completed successfully")
            return True

        except Exception as e:
            logger.error(f"Daily content generation failed: {str(e)}", exc_info=True)
            try:
                self.telegram_bot.send_error_notification("Content Generator", str(e))
            except Exception as notify_error:
                logger.error(f"Failed to send error notification: {str(notify_error)}")
            return False


# Service instance
_content_generator: Optional[ContentGenerator] = None


def get_content_generator() -> ContentGenerator:
    """Get or create content generator instance"""
    global _content_generator
    if _content_generator is None:
        _content_generator = ContentGenerator()
    return _content_generator


def run_content_generation() -> None:
    """Run content generation (for scheduler)"""
    generator = get_content_generator()
    generator.run_daily_content_generation()


# Example usage
if __name__ == "__main__":
    # Test content generator
    generator = ContentGenerator()

    # Test blog generation
    blog = generator.generate_blog_post(
        topic="Python 자동화의 미래",
        keywords=["Python", "자동화", "AI"]
    )

    if blog:
        print(f"Generated blog: {blog.title}")
        print(f"Word count: {blog.word_count}")
        generator.save_content(blog)
