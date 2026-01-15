# DAIP 설치 및 설정 가이드

이 문서는 Daily Automated Intelligence Platform (DAIP)의 상세한 설치 및 설정 방법을 안내합니다.

## 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [Telegram Bot 설정](#telegram-bot-설정)
3. [로컬 설치](#로컬-설치)
4. [Docker 설치](#docker-설치)
5. [GitHub Actions 설정](#github-actions-설정)
6. [환경 변수 설정](#환경-변수-설정)
7. [서비스별 설정](#서비스별-설정)
8. [트러블슈팅](#트러블슈팅)

## 시스템 요구사항

### 최소 요구사항
- **운영체제**: Linux, macOS, Windows 10/11
- **Python**: 3.11 이상
- **메모리**: 최소 2GB RAM
- **저장공간**: 500MB 이상

### 권장 요구사항
- **운영체제**: Ubuntu 22.04 LTS 또는 macOS
- **Python**: 3.11
- **메모리**: 4GB RAM 이상
- **저장공간**: 2GB 이상
- **네트워크**: 안정적인 인터넷 연결

## Telegram Bot 설정

### 1. Bot 생성

1. Telegram에서 [@BotFather](https://t.me/BotFather)를 검색
2. `/newbot` 명령어 입력
3. Bot 이름 입력 (예: "DAIP News Bot")
4. Bot 사용자명 입력 (예: "daip_news_bot")
5. BotFather가 제공하는 **Token**을 복사하여 저장

### 2. Chat ID 확인

방법 1: Bot과 대화 시작
```bash
# 1. Bot과 대화 시작 (메시지 전송)
# 2. 브라우저에서 다음 URL 접속
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates

# 3. 응답에서 "chat":{"id": 숫자} 찾기
```

방법 2: @userinfobot 사용
```
1. @userinfobot과 대화 시작
2. /start 명령어 입력
3. Chat ID 확인
```

## 로컬 설치

### 1. 저장소 클론

```bash
git clone https://github.com/waterfirst/daily_news.git
cd daily_news
```

### 2. Python 가상환경 설정

**Unix/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. 의존성 설치

```bash
# pip 업그레이드
pip install --upgrade pip

# 의존성 설치
pip install -r requirements.txt
```

### 4. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 원하는 에디터 사용
```

필수 환경 변수:
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

### 5. 애플리케이션 실행

```bash
# 전체 서비스 실행
python main.py

# 특정 서비스만 실행
python main.py etf        # ETF 분석만
python main.py news       # 뉴스 스크래핑만
python main.py beauty     # 화장품 뉴스만
```

## Docker 설치

### 1. Docker 및 Docker Compose 설치

**Ubuntu:**
```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo apt-get install docker-compose-plugin
```

**macOS:**
```bash
# Docker Desktop 설치
brew install --cask docker
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 환경 변수 편집
nano .env
```

### 3. Docker 이미지 빌드 및 실행

```bash
# 이미지 빌드
cd docker
docker-compose build

# 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f daip

# 컨테이너 중지
docker-compose down
```

### 4. Docker 유용한 명령어

```bash
# 컨테이너 상태 확인
docker-compose ps

# 컨테이너 재시작
docker-compose restart

# 로그 확인 (실시간)
docker-compose logs -f

# 컨테이너 내부 접속
docker-compose exec daip bash

# 볼륨 확인
docker volume ls
```

## GitHub Actions 설정

### 1. Repository Secrets 설정

1. GitHub 저장소로 이동
2. `Settings` > `Secrets and variables` > `Actions`
3. `New repository secret` 클릭
4. 다음 Secrets 추가:

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ANTHROPIC_API_KEY=your_anthropic_key (선택)
STOCK_API_KEY=your_stock_api_key (선택)
NEWS_API_KEY=your_news_api_key (선택)
NAVER_CLIENT_ID=your_naver_id (선택)
NAVER_CLIENT_SECRET=your_naver_secret (선택)
```

### 2. Workflow 확인

Workflow 파일들이 `.github/workflows/` 디렉토리에 있는지 확인:
- `schedule-etf.yml` - ETF 분석 (매시간)
- `schedule-news.yml` - 뉴스 스크래핑 (하루 3회)
- `schedule-industry-news.yml` - 산업별 뉴스

### 3. 수동 실행

1. GitHub 저장소의 `Actions` 탭 이동
2. 원하는 Workflow 선택
3. `Run workflow` 버튼 클릭

### 4. 스케줄 수정

Workflow 파일의 cron 표현식 수정:
```yaml
on:
  schedule:
    - cron: '0 1,3,5 * * *'  # UTC 시간 기준
```

**Cron 시간 변환:**
- KST = UTC + 9시간
- 예: KST 10:00 → UTC 01:00

## 환경 변수 설정

### 필수 환경 변수

```bash
# Telegram (필수)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# 데이터베이스 (선택, 기본값 사용 가능)
DATABASE_URL=sqlite:///data/database.db

# 타임존 (선택, 기본값: Asia/Seoul)
TIMEZONE=Asia/Seoul
```

### 선택 환경 변수

```bash
# AI API Keys (콘텐츠 생성 서비스 사용 시)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# 금융 데이터 APIs
STOCK_API_KEY=your_stock_api_key
YAHOO_FINANCE_API_KEY=your_yahoo_key

# 뉴스 APIs
NEWS_API_KEY=your_news_api_key
NAVER_CLIENT_ID=your_naver_id
NAVER_CLIENT_SECRET=your_naver_secret

# 로깅
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/daip.log

# 서비스 활성화/비활성화
ETF_SERVICE_ENABLED=true
NEWS_SERVICE_ENABLED=true
BEAUTY_NEWS_ENABLED=true
DISPLAY_NEWS_ENABLED=true
SEMICONDUCTOR_NEWS_ENABLED=true

# 디버그 모드
DEBUG=false
```

## 서비스별 설정

### ETF 분석 서비스

**설정 파일:** `src/config.py` > `ETFConfig`

```python
# 실행 시간 (KST)
SCHEDULE_TIMES = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]

# 분석 파라미터
LOOKBACK_DAYS = 30              # 과거 데이터 조회 일수
STOCHASTIC_PERIOD = 14          # Stochastic 기간
OVERSOLD_THRESHOLD = 20         # 과매도 기준
OVERBOUGHT_THRESHOLD = 80       # 과매수 기준
TOP_N_RECOMMENDATIONS = 5       # 추천 종목 수

# ETF 티커 (추가/제거 가능)
ETF_TICKERS = [
    "069500.KS",  # KODEX 200
    "102110.KS",  # TIGER 200
    "251350.KS",  # KODEX 코스닥150
    "091160.KS",  # KODEX 반도체
    "091180.KS",  # KODEX 은행
]
```

### 뉴스 스크래핑 서비스

**설정 파일:** `src/config.py` > `NewsConfig`

```python
# 실행 시간
SCHEDULE_TIMES = ["10:00", "12:00", "14:00"]

# 카테고리 (추가/제거 가능)
CATEGORIES = ["정치", "경제", "사회", "IT", "AI"]

# 수집 뉴스 수
TOP_N_NEWS = 5

# 중복 제거 threshold
DUPLICATE_THRESHOLD = 0.8
```

### 산업별 뉴스 서비스

각 서비스의 실행 시간 및 소스 설정:

**화장품 뉴스:**
```python
SCHEDULE_TIMES = ["11:00", "15:00"]
SOURCES = {
    "cosme": "https://www.cosme.net",
    "japanese_pr": "https://prtimes.jp/...",
}
```

**디스플레이 뉴스:**
```python
SCHEDULE_TIMES = ["10:00", "14:00"]
COUNTRIES = ["한국", "중국", "일본", "대만"]
```

**반도체/로봇/바이오 뉴스:**
```python
SCHEDULE_TIMES = ["09:00", "13:00"]
CATEGORIES = ["반도체", "로봇", "바이오"]
```

## 트러블슈팅

### 문제 1: Telegram 메시지가 전송되지 않음

**해결 방법:**
```bash
# Bot Token 확인
echo $TELEGRAM_BOT_TOKEN

# Chat ID 확인
echo $TELEGRAM_CHAT_ID

# Bot과 대화 시작했는지 확인
# Telegram에서 Bot에게 /start 메시지 전송

# 로그 확인
tail -f logs/daip.log
```

### 문제 2: yfinance 데이터 가져오기 실패

**해결 방법:**
```bash
# yfinance 재설치
pip install --upgrade yfinance

# 네트워크 연결 확인
ping finance.yahoo.com

# 프록시 설정 (필요시)
export HTTP_PROXY=http://proxy:port
```

### 문제 3: 웹 스크래핑 실패

**원인:**
- User-Agent 차단
- 웹사이트 구조 변경
- Rate limiting

**해결 방법:**
```python
# User-Agent 변경 (src/services/news_scraper.py)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...'
}

# 요청 간격 추가
import time
time.sleep(1)  # 1초 대기
```

### 문제 4: Docker 컨테이너 시작 실패

**해결 방법:**
```bash
# 로그 확인
docker-compose logs daip

# 환경 변수 확인
docker-compose config

# 컨테이너 재빌드
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 문제 5: GitHub Actions 실패

**해결 방법:**
```bash
# 1. Secrets 설정 확인
# Settings > Secrets and variables > Actions

# 2. Workflow 로그 확인
# Actions 탭에서 실패한 job 클릭

# 3. 의존성 문제 해결
# requirements.txt의 버전 확인
```

### 문제 6: 한글 인코딩 문제

**해결 방법:**
```bash
# 환경 변수 설정
export LANG=ko_KR.UTF-8
export LC_ALL=ko_KR.UTF-8

# Python 파일 상단에 추가
# -*- coding: utf-8 -*-
```

## 로그 확인

### 로그 파일 위치
```
logs/
├── daip.log           # 메인 로그
└── daip.log.1         # 로테이션된 로그
```

### 로그 레벨별 확인
```bash
# 모든 로그
tail -f logs/daip.log

# ERROR 이상만
grep "ERROR\|CRITICAL" logs/daip.log

# 특정 서비스 로그
grep "daip.etf" logs/daip.log
```

## 성능 최적화

### 1. 캐싱 활성화
```bash
CACHE_ENABLED=true
CACHE_TTL=3600  # 1시간
```

### 2. Rate Limiting
```bash
RATE_LIMIT_ENABLED=true
MAX_REQUESTS_PER_MINUTE=30
```

### 3. 병렬 처리 (향후 구현)
```python
# asyncio 사용
import asyncio
```

## 다음 단계

설치가 완료되었다면:

1. [README.md](../README.md)에서 사용법 확인
2. [ARCHITECTURE.md](ARCHITECTURE.md)에서 시스템 구조 이해
3. 테스트 실행: `pytest tests/`
4. 단일 서비스 테스트: `python main.py etf`

## 지원

문제가 지속되는 경우:
- GitHub Issues: https://github.com/waterfirst/daily_news/issues
- 문서 참조: [ARCHITECTURE.md](ARCHITECTURE.md)

---

**설치 중 문제가 발생하면 GitHub Issue를 생성해주세요!**
