# 🚀 Kiwoom Trading System

**AI-powered Korean stock trading system using Kiwoom OpenAPI+, KRX market data, and OpenAI analysis**

## 📋 Overview

This system automatically:
1. Retrieves stocks from your **'10stars'** screening condition in Kiwoom
2. Fetches additional market data from **KRX Market Data API**
3. Performs **AI-powered financial analysis** using OpenAI GPT
4. Delivers **comprehensive trading recommendations** via Slack

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Kiwoom API     │    │   KRX API       │    │   OpenAI API    │
│  (Stock Data)   │    │ (Market Data)   │    │ (AI Analysis)   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    Main Orchestrator      │
                    │     (main.py)            │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    Slack Notifier        │
                    │   (Trading Alerts)       │
                    └─────────────────────────────┘
```

## 🛠️ Components

### Core Modules

| Module | Purpose | Features |
|--------|---------|----------|
| `main.py` | System orchestrator | Main loop, error handling, graceful shutdown |
| `kiwoom_api.py` | Kiwoom API integration | Stock screening, real-time data, account info |
| `krx_api.py` | KRX market data | Financial indicators, sector info, market indices |
| `ai_analyzer.py` | AI-powered analysis | Buy/sell recommendations, portfolio analysis |
| `slack_notifier.py` | Notification system | Rich formatted alerts, error notifications |
| `config.py` | Configuration management | Environment variables, validation |

### Key Features

- **🔍 Automated Stock Screening**: Uses your '10stars' condition
- **🤖 AI Analysis**: GPT-4 powered financial analysis with reasoning
- **📊 Rich Market Data**: KRX integration for comprehensive metrics
- **📱 Slack Integration**: Beautiful formatted notifications
- **🔄 Real-time Operation**: Continuous monitoring during market hours
- **🛡️ Error Handling**: Comprehensive error recovery and notifications
- **🧪 Test Mode**: Safe development without live trading

## 📦 Installation

### Prerequisites

- **Windows 10/11** (required for Kiwoom API)
- **Python 3.10+ (32-bit)** (mandatory for Kiwoom compatibility)
- **Kiwoom Hero HTS** installed and running
- **Active Kiwoom Securities account**

### Quick Setup

1. **Clone and setup**:
   ```bash
   cd C:\kiwoom
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   # Edit .env file with your credentials
   notepad .env
   ```

3. **Validate setup**:
   ```bash
   python config.py
   ```

4. **Test run**:
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Kiwoom API
KIWOOM_USER_ID=your_kiwoom_id
KIWOOM_PASSWORD=your_password
KIWOOM_CERT_PASSWORD=your_cert_password

# OpenAI
OPENAI_API_KEY=sk-your_openai_key

# Slack
SLACK_BOT_TOKEN=xoxb-your_bot_token
SLACK_CHANNEL=#trading-alerts

# Trading
SCREENING_CONDITION_NAME=10stars
MAX_STOCKS_TO_ANALYZE=10
TRADING_MODE=TEST  # TEST or LIVE
ANALYSIS_INTERVAL=300  # 5 minutes
```

### Required API Setup

#### 1. Kiwoom Securities
- Install Kiwoom OpenAPI+ from [Kiwoom website](https://www3.kiwoom.com/)
- Create and save your '10stars' screening condition in Kiwoom HTS
- Ensure HTS is running and logged in

#### 2. OpenAI
- Get API key from [OpenAI Platform](https://platform.openai.com/)
- Ensure sufficient credits for API usage

#### 3. Slack
- Create Slack Bot at [Slack Apps](https://api.slack.com/apps)
- Add bot to your trading channel
- Grant `chat:write` permissions

#### 4. KRX Market Data (Optional)
- Free access to KRX market data APIs
- Enhanced with financial indicators and sector data

## 🚀 Usage

### Running the System

```bash
# Start with automatic environment setup
start.bat

# Or run directly
python main.py
```

### System Behavior

**Market Hours (9:00-15:30 KST)**:
- Continuous monitoring every 5 minutes
- Automatic stock screening and analysis
- Real-time Slack notifications

**Outside Market Hours**:
- System sleeps and waits for market open
- Error monitoring and system status updates

### Test vs Live Mode

**TEST Mode** (`TRADING_MODE=TEST`):
- Uses mock data and APIs
- Safe for development and testing
- No actual API calls to external services

**LIVE Mode** (`TRADING_MODE=LIVE`):
- Full integration with all APIs
- Real trading analysis and alerts
- Requires all API credentials

## 📊 Output Examples

### Stock Analysis Notification

```
🔍 AI 주식 분석 결과
분석 시간: 2024-01-15 10:30:00 | 분석 종목: 10개

🟢 삼성전자 (005930)
추천: BUY | 신뢰도: 85%
목표가: 75,000원 | 투자기간: MEDIUM

분석 요약:
강력한 반도체 사이클 회복과 AI 수요 증가로 인한 메모리 반도체 가격 상승이 예상됩니다...

주요 요인:
• AI 반도체 수요 급증
• 메모리 가격 반등 신호
• 안정적인 현금흐름

📊 분석 요약
🟢 매수: 6개 | 🔴 매도: 2개 | 🟡 보유: 2개
```

### Portfolio Analysis

```
📊 포트폴리오 분석
포트폴리오 점수: 7.5/10 | 리스크 수준: MODERATE
분산 점수: 8.0/10 | 시장 전망: 낙관적

💡 추천사항:
• 기술주 비중 조정 고려
• 방어주 포지션 증대
• 배당주 추가 검토

🏭 섹터 분포:
• Technology: 40%
• Finance: 30% 
• Manufacturing: 30%
```

## 🔧 Development

### Project Structure

```
kiwoom/
├── main.py              # Main orchestrator
├── config.py            # Configuration management
├── kiwoom_api.py        # Kiwoom API integration
├── krx_api.py           # KRX market data
├── ai_analyzer.py       # OpenAI analysis
├── slack_notifier.py    # Slack notifications
├── requirements.txt     # Dependencies
├── .env                 # Environment variables
├── start.bat           # Windows launcher
└── logs/               # System logs
```

### Adding New Features

1. **New Analysis Indicators**:
   - Extend `ai_analyzer.py` with new analysis methods
   - Update prompt engineering for better insights

2. **Additional Data Sources**:
   - Create new API integration modules
   - Follow the pattern of `krx_api.py`

3. **Enhanced Notifications**:
   - Extend `slack_notifier.py` with new block types
   - Add support for other platforms (Discord, Teams, etc.)

### Testing

```bash
# Configuration validation
python config.py

# Component testing (requires actual APIs)
python -c "from kiwoom_api import KiwoomAPI; api = KiwoomAPI(); print('Kiwoom:', api.connect())"
python -c "from ai_analyzer import AIStockAnalyzer; ai = AIStockAnalyzer(); print('OpenAI: OK')"
python -c "from slack_notifier import SlackNotifier; slack = SlackNotifier(); print('Slack: OK')"
```

## 📋 Troubleshooting

### Common Issues

**Kiwoom API Connection Failed**:
```
Solution: 
1. Ensure 32-bit Python is installed
2. Run as Administrator
3. Verify Kiwoom HTS is logged in
4. Re-register OCX: regsvr32 "C:\OpenAPI\KHOpenAPI.dll"
```

**OpenAI API Errors**:
```
Solution:
1. Check API key format (starts with 'sk-')
2. Verify account has sufficient credits
3. Check rate limits and quotas
```

**Slack Notifications Failed**:
```
Solution:
1. Verify bot token format (starts with 'xoxb-')
2. Ensure bot is added to target channel
3. Check bot permissions (chat:write)
```

**'10stars' Condition Not Found**:
```
Solution:
1. Create condition in Kiwoom HTS
2. Save with exact name '10stars'
3. Verify condition loads in HTS
```

### Logs and Debugging

- **System logs**: `logs/kiwoom_trading.log`
- **Debug mode**: Set `LOG_LEVEL=DEBUG` in `.env`
- **Error notifications**: Automatic Slack alerts for system errors

## 🔒 Security

- **Never commit `.env`** file to version control
- **Rotate API keys** regularly
- **Use separate accounts** for testing
- **Monitor API usage** and costs
- **Run with minimal Windows permissions**

## 📈 Performance

- **Analysis frequency**: Configurable (default: 5 minutes)
- **API rate limits**: Respected for all services
- **Memory usage**: Optimized for continuous operation
- **Error recovery**: Automatic reconnection and retry logic

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Test with mock APIs first
4. Submit pull request with documentation

## 📞 Support

- **System errors**: Check `logs/kiwoom_trading.log`
- **API issues**: Refer to respective API documentation
- **Configuration**: Run `python config.py` for validation

---

**⚠️ Disclaimer**: This system is for educational and research purposes. Always perform due diligence before making investment decisions. Past performance does not guarantee future results.