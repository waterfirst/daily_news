# DAIP 시스템 아키텍처

## 개요

Daily Automated Intelligence Platform (DAIP)는 마이크로서비스 아키텍처를 기반으로 한 자동화 플랫폼입니다.

## 시스템 구성요소

### 1. 서비스 레이어 (Service Layer)

각 서비스는 독립적으로 실행 가능하며, 특정 도메인에 특화되어 있습니다.

#### ETF Analyzer (`src/services/etf_analyzer.py`)
- **책임**: 한국 ETF 시장 분석 및 투자 신호 생성
- **입력**: Yahoo Finance API를 통한 ETF 가격 데이터
- **출력**: Stochastic 지표 기반 매수/매도 신호
- **실행 주기**: 09:00-15:00, 매시간 (월-금)

#### News Scraper (`src/services/news_scraper.py`)
- **책임**: 종합 뉴스 수집 및 분석
- **입력**: Naver News, Google News RSS
- **출력**: 카테고리별 상위 뉴스 5개
- **실행 주기**: 10:00, 12:00, 14:00

#### Industry News Scrapers (`src/services/industry_news.py`)
- **BeautyNewsScraper**: 일본 화장품 산업 뉴스
- **DisplayNewsScraper**: 한중일대 디스플레이 산업 뉴스
- **SemiconductorNewsScraper**: 미국/한국 반도체/로봇/바이오 뉴스

### 2. 데이터 레이어 (Data Layer)

#### 데이터 소스
```
External APIs
├── Yahoo Finance (yfinance)
│   └── ETF 가격 데이터
├── News APIs
│   ├── Naver News
│   ├── Google News
│   └── RSS Feeds
└── Web Scraping
    ├── BeautifulSoup4
    └── Selenium (동적 콘텐츠)
```

#### 데이터 모델
```python
# ETF 데이터 모델
@dataclass
class ETFData:
    ticker: str
    name: str
    current_price: float
    change_pct: float
    stochastic_k: float
    stochastic_d: float
    signal: str  # BUY, SELL, HOLD, WATCH

# 뉴스 데이터 모델
@dataclass
class NewsArticle:
    title: str
    source: str
    url: str
    category: str
    sentiment: str  # positive, negative, neutral
    keywords: List[str]
```

### 3. 스케줄링 레이어 (Scheduling Layer)

#### JobScheduler (`src/schedulers/job_scheduler.py`)
- **기반**: APScheduler
- **기능**:
  - Cron 스타일 스케줄링
  - Interval 기반 스케줄링
  - 작업 이벤트 리스닝 (성공/실패)
  - 동적 작업 추가/제거

#### ServiceScheduler
- **책임**: 각 서비스의 스케줄 관리
- **설정**:
```python
# ETF 서비스: 매시간 실행 (월-금, 09:00-15:00)
scheduler.add_time_based_job(
    etf_service_func,
    job_id="etf_analysis",
    times=["09:00", "10:00", ..., "15:00"],
    day_of_week="mon-fri"
)
```

### 4. 통신 레이어 (Communication Layer)

#### TelegramBot (`src/telegram_bot.py`)
- **책임**: 분석 결과 및 알림 전송
- **기능**:
  - 서비스별 포맷팅된 리포트 전송
  - 에러 알림
  - 시스템 시작/종료 알림

#### 메시지 포맷
```
📈 09:00 ETF 추천 리포트
━━━━━━━━━━━━━━━━━━━━━━━
🟢 1. KODEX 200 (+3.2%) | Stoch: 65.8
   신호: BUY
...
```

### 5. 설정 레이어 (Configuration Layer)

#### Config (`src/config.py`)
- **기반**: Pydantic Settings
- **기능**:
  - 환경 변수 검증
  - 타입 안전성
  - 서비스별 설정 클래스

```python
class Settings(BaseSettings):
    telegram_bot_token: str
    etf_service_enabled: bool = True
    news_service_enabled: bool = True
    # ...
```

### 6. 로깅 레이어 (Logging Layer)

#### Logger (`src/logger.py`)
- **콘솔 출력**: 컬러 로깅 (colorlog)
- **파일 출력**: 구조화된 로그 (JSON/텍스트)
- **레벨**: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 데이터 흐름

### ETF 분석 플로우
```
1. 스케줄러 트리거 (매시간)
   ↓
2. ETFAnalyzer.run()
   ↓
3. yfinance API 호출
   ↓
4. Stochastic 계산
   ↓
5. 신호 생성 (BUY/SELL/HOLD)
   ↓
6. Telegram Bot으로 전송
   ↓
7. 사용자 수신
```

### 뉴스 스크래핑 플로우
```
1. 스케줄러 트리거
   ↓
2. NewsScraper.run()
   ↓
3. 웹 스크래핑 (BeautifulSoup)
   ↓
4. 감정 분석 (TextBlob)
   ↓
5. 중복 제거
   ↓
6. 상위 N개 선택
   ↓
7. Telegram Bot으로 전송
```

## 배포 아키텍처

### GitHub Actions 기반
```
GitHub Actions
├── schedule-etf.yml
│   └── 매시간 ETF 분석 실행
├── schedule-news.yml
│   └── 하루 3회 뉴스 수집
└── schedule-industry-news.yml
    └── 산업별 뉴스 수집
```

### Docker 배포
```
Docker Container
├── Application Layer (main.py)
├── Service Layer (services/)
├── Data Volume (SQLite DB)
└── Log Volume (logs/)
```

## 확장성 고려사항

### 수평 확장
- 각 서비스는 독립적으로 스케일 가능
- 메시지 큐 (Redis, RabbitMQ) 도입 가능

### 수직 확장
- 데이터베이스: SQLite → PostgreSQL
- 캐싱: 메모리 → Redis
- 스토리지: 로컬 → S3

## 보안

### API 키 관리
- 환경 변수로 분리
- GitHub Secrets 사용
- .env 파일은 .gitignore에 포함

### 데이터 보호
- HTTPS 통신
- API 요청 속도 제한
- 에러 로그에서 민감 정보 제거

## 모니터링

### 현재 구현
- 로그 파일 기록
- Telegram 에러 알림
- GitHub Actions 실행 로그

### 향후 계획
- Sentry 통합
- Prometheus + Grafana
- 시스템 메트릭 수집

## 성능 최적화

### 캐싱 전략
- API 응답 캐싱 (TTL: 1시간)
- 뉴스 중복 체크용 해시 캐시

### 비동기 처리
- 향후 asyncio 도입 고려
- 병렬 뉴스 스크래핑

## 기술 스택 요약

| 계층 | 기술 |
|------|------|
| 언어 | Python 3.11+ |
| 웹 프레임워크 | FastAPI (향후) |
| 스케줄링 | APScheduler |
| 데이터베이스 | SQLite (현재), PostgreSQL (향후) |
| 메시징 | Telegram Bot API |
| 웹 스크래핑 | BeautifulSoup4, Selenium |
| 데이터 분석 | pandas, numpy |
| NLP | TextBlob |
| 금융 데이터 | yfinance |
| 컨테이너 | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| 로깅 | colorlog, python-json-logger |

## 다이어그램

### 시스템 컴포넌트 다이어그램
```
┌──────────────────────────────────────────────┐
│           Main Application (main.py)          │
└──────────────────┬───────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌───────────────┐     ┌──────────────┐
│ Service       │     │ Scheduler    │
│ Scheduler     │────▶│ (APScheduler)│
└───────┬───────┘     └──────────────┘
        │
        ├─────────────┬─────────────┬──────────────┐
        ▼             ▼             ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ ETF      │  │ News     │  │ Beauty   │  │ Display  │
│ Analyzer │  │ Scraper  │  │ News     │  │ News     │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │              │              │
     └─────────────┴──────────────┴──────────────┘
                   │
                   ▼
           ┌──────────────┐
           │ Telegram Bot │
           └──────────────┘
```

이 아키텍처는 모듈화, 확장성, 유지보수성을 중심으로 설계되었습니다.
