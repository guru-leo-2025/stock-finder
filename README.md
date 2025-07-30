# 🚀 AI-Powered Korean Stock Trading System

AI 기반 한국 주식 자동매매 시스템으로 키움증권 API와 OpenAI를 활용한 지능형 트레이딩 플랫폼입니다.

## ✨ 주요 기능

- 🤖 **AI 기반 주식 분석**: OpenAI GPT-4를 활용한 지능형 기술적 분석
- 📊 **실시간 데이터 처리**: 키움증권 OpenAPI를 통한 실시간 주가 및 거래 데이터
- 🔍 **종목 스크리닝**: 사용자 정의 조건으로 투자 대상 종목 자동 선별
- 📱 **Slack 알림**: 거래 신호 및 분석 결과 실시간 알림
- 📈 **기술적 분석**: RSI, MACD, 볼린저 밴드 등 다양한 기술적 지표 분석

## 🏗️ 시스템 구조

```
kiwoom/
├── main.py                 # 메인 애플리케이션
├── kiwoom_api.py           # 키움증권 API 인터페이스
├── ai_analyzer.py          # AI 기반 주식 분석 엔진
├── technical_analyzer.py   # 기술적 분석 모듈
├── slack_notifier.py       # Slack 알림 시스템
├── config.py              # 설정 관리
├── requirements.txt       # 의존성 패키지
├── start.bat             # Windows 실행 스크립트
├── data/                 # 분석 데이터 저장소
└── logs/                 # 로그 파일 저장소
```

## 🔧 설치 및 설정

### 1. 시스템 요구사항
- Windows 10/11 (키움증권 OpenAPI 지원)
- Python 3.10+
- 키움증권 계좌 및 OpenAPI 신청

### 2. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/guru-leo-2025/stock-finder.git
cd stock-finder

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env` 파일을 생성하고 다음 정보를 입력하세요:

```env
# Kiwoom API
KIWOOM_USER_ID=your_user_id
KIWOOM_PASSWORD=your_password
KIWOOM_CERT_PASSWORD=your_cert_password
SCREENING_CONDITION_NAME=10stars

# OpenAI API
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini-2024-07-18
OPENAI_MAX_TOKENS=2000

# Slack
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_CHANNEL=your_channel_name
```

## 🚀 사용법

### Windows에서 실행
```bash
# 배치 파일로 실행
start.bat

# 또는 Python으로 직접 실행
python main.py
```

### 주요 모듈 사용 예시

```python
from kiwoom_api import KiwoomAPI
from ai_analyzer import AIStockAnalyzer
from technical_analyzer import TechnicalAnalyzer

# 키움 API 초기화
kiwoom = KiwoomAPI()

# AI 분석기 초기화
ai_analyzer = AIStockAnalyzer()

# 기술적 분석기 초기화
tech_analyzer = TechnicalAnalyzer()

# 종목 분석 실행
analysis_result = await ai_analyzer.analyze_stock("005930")  # 삼성전자
```

## 📊 기능 상세

### AI 분석 엔진
- **다중 지표 분석**: RSI, MACD, 볼린저 밴드, 이동평균선 등
- **AI 모델 선택**: 기본값 `gpt-4o-mini-2024-07-18` (비용 효율적)
- **패턴 인식**: 차트 패턴 및 기술적 신호 자동 감지
- **위험도 평가**: AI 기반 리스크 스코어링

#### 📝 지원 OpenAI 모델
- `gpt-4o-mini-2024-07-18` (기본값, 비용 효율적)
- `gpt-4o` (고성능, 높은 비용)
- `gpt-4-turbo` (균형잡힌 성능)
- `gpt-4` (표준 GPT-4 모델)

환경변수 `OPENAI_MODEL`로 변경 가능합니다.

### 실시간 모니터링
- 실시간 주가 변동 추적
- 거래량 급증 종목 감지
- 사용자 정의 조건 알림
- 포트폴리오 성과 추적

### Slack 통합
- 실시간 거래 신호 알림
- 일일/주간 성과 리포트
- 시장 오픈/마감 알림
- 긴급 상황 알림

## 📈 분석 결과 예시

시스템은 다음과 같은 형태의 분석 결과를 제공합니다:

```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "analysis_time": "2025-01-30 14:30:00",
  "technical_indicators": {
    "rsi": 65.4,
    "macd_signal": "BUY",
    "bollinger_position": "UPPER"
  },
  "ai_recommendation": {
    "action": "BUY",
    "confidence": 0.85,
    "target_price": 75000,
    "stop_loss": 68000
  },
  "risk_assessment": {
    "risk_level": "MEDIUM",
    "volatility": 0.23
  }
}
```

## ⚠️ 주의사항

- 본 시스템은 투자 참고용이며, 실제 투자 결정은 사용자 책임입니다
- 키움증권 OpenAPI 사용 약관을 준수하세요
- 충분한 백테스팅 후 실제 거래에 적용하세요
- API 사용량 제한을 확인하고 관리하세요

## 🔒 보안

- API 키와 민감한 정보는 환경변수로 관리
- 로그 파일에서 개인정보 제외
- HTTPS 통신 사용
- 정기적인 의존성 업데이트 권장

## 📞 지원 및 문의

- **Issues**: [GitHub Issues](https://github.com/guru-leo-2025/stock-finder/issues)
- **개발자**: guru.leo.2025@gmail.com

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 제공됩니다.

---
**⚡ Happy Trading with AI! ⚡**