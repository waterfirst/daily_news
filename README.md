# Daily Automated Intelligence Platform (DAIP)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**금융, 뉴스, 콘텐츠 생성을 자동화하여 매일 시간대별 맞춤형 정보를 제공하는 통합 플랫폼**

## 📋 프로젝트 개요

DAIP는 AI 시대의 자동화 비즈니스 플랫폼으로, 다음 기능들을 제공합니다:

- 📈 **ETF 분석 및 추천** - 한국 ETF 시장 분석 및 투자 신호 생성
- 📰 **종합 뉴스 스크래핑** - 정치, 경제, IT, AI 등 다양한 분야 뉴스 수집
- 💄 **화장품 산업 뉴스** - 일본 뷰티 시장 동향 및 신기술 분석
- 📱 **디스플레이 산업 뉴스** - 한중일대 디스플레이 기술 및 시장 정보
- 🔬 **반도체/로봇/바이오 뉴스** - 미국 및 한국 첨단 산업 동향
- 📱 **Telegram 실시간 알림** - 모든 분석 결과를 텔레그램으로 즉시 전송

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot (메시지 전송)                  │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│           서비스 레이어 (7개 자동화 서비스)                      │
├─────────────────────────────────────────────────────────────┤
│ 1. ETF분석      2. 뉴스스크랩    3. 콘텐츠생성              │
│ 4. 웹앱개발    5. 화장품뉴스    6. 디스플레이뉴스             │
│ 7. 반도체/로봇/바이오 뉴스                                    │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│           데이터 레이어 (API, 크롤링, DB)                     │
├─────────────────────────────────────────────────────────────┤
│ • Yahoo Finance API (ETF)                                   │
│ • BeautifulSoup 크롤링 (뉴스)                                │
│ • SQLite/PostgreSQL (로컬 DB)                               │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│           실행 레이어 (APScheduler, GitHub Actions)          │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 빠른 시작

### 필수 요구사항

- Python 3.11 이상
- pip 또는 Poetry
- Telegram Bot Token (BotFather에서 생성)
- (선택) Docker & Docker Compose

### 설치

1. **저장소 클론**
```bash
git clone https://github.com/waterfirst/daily_news.git
cd daily_news
```

2. **가상 환경 생성 및 활성화**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **환경 변수 설정**
```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 입력
```

5. **애플리케이션 실행**
```bash
python main.py
```

### Docker로 실행

```bash
cd docker
docker-compose up -d
```

## ⚙️ 설정

### 환경 변수

`.env` 파일에서 다음 설정을 구성하세요:

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# API Keys
ANTHROPIC_API_KEY=your_anthropic_key
STOCK_API_KEY=your_stock_api_key

# Service Configuration
ETF_SERVICE_ENABLED=true
NEWS_SERVICE_ENABLED=true
BEAUTY_NEWS_ENABLED=true
DISPLAY_NEWS_ENABLED=true
SEMICONDUCTOR_NEWS_ENABLED=true
```

자세한 설정은 [SETUP.md](docs/SETUP.md)를 참조하세요.

## 📅 스케줄

### ETF 분석
- **실행 시간**: 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00 (월-금)
- **내용**: Stochastic 지표 기반 매수/매도 신호 생성

### 종합 뉴스
- **실행 시간**: 10:00, 12:00, 14:00 (매일)
- **카테고리**: 정치, 경제, 사회, IT, AI

### 산업별 뉴스
- **화장품**: 11:00, 15:00
- **디스플레이**: 10:00, 14:00
- **반도체/로봇/바이오**: 09:00, 13:00

## 🛠️ 개발

### 프로젝트 구조

```
daily-ai-platform/
├── src/                    # 소스 코드
│   ├── services/          # 서비스 구현
│   ├── models/            # 데이터 모델
│   ├── schedulers/        # 스케줄러
│   └── utils/             # 유틸리티
├── tests/                 # 테스트 코드
├── docker/                # Docker 설정
├── .github/workflows/     # GitHub Actions
└── docs/                  # 문서
```

### 단일 서비스 실행

```bash
# ETF 분석만 실행
python main.py etf

# 뉴스 스크래핑만 실행
python main.py news

# 화장품 뉴스만 실행
python main.py beauty
```

### 테스트

```bash
pytest tests/
```

## 📊 서비스별 상세

### 1. ETF 분석 서비스

- **데이터 소스**: yfinance (Yahoo Finance)
- **분석 지표**: Stochastic Oscillator (%K, %D)
- **추천 로직**:
  - Oversold (< 20) + Bullish Crossover = BUY
  - Overbought (> 80) + Bearish Crossover = SELL
- **출력**: 상위 5개 ETF 추천

### 2. 뉴스 스크래핑

- **소스**: Naver News, Google News, Medium
- **처리**: 중복 제거, 감정 분석, 키워드 추출
- **카테고리**: 정치, 경제, 사회, IT, AI

### 3-5. 산업별 뉴스

각 산업별 특화된 뉴스 소스에서 정보 수집:
- 화장품: 일본 cosme.net, 특허청
- 디스플레이: 한중일대 기술 매체
- 반도체/로봇/바이오: WSJ, Reuters, 한국 IT 매체

## 🤝 기여

프로젝트 기여를 환영합니다! 다음 단계를 따라주세요:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📧 연락처

프로젝트 관리자: waterfirst

프로젝트 링크: [https://github.com/waterfirst/daily_news](https://github.com/waterfirst/daily_news)

## 🙏 감사의 말

- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance 데이터
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram 봇
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - 웹 스크래핑
- [APScheduler](https://apscheduler.readthedocs.io/) - 작업 스케줄링

## 📈 로드맵

- [x] Phase 1: Core Infrastructure
- [x] Phase 2: 기본 서비스 구현 (ETF, 뉴스, 산업별 뉴스)
- [ ] Phase 3: AI 콘텐츠 생성 서비스
- [ ] Phase 4: 대학생 웹앱 개발
- [ ] Phase 5: 클라우드 배포 및 최적화
- [ ] Phase 6: 수익화 전략 실행

---

**Made with ❤️ by waterfirst**
