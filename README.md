# 🚀 AI-Powered Korean Stock Trading System

An intelligent trading platform that combines Kiwoom Securities API with OpenAI for automated Korean stock market analysis and trading.

## ✨ Key Features

- 🤖 **AI-Enhanced Stock Analysis**: Intelligent technical analysis powered by OpenAI GPT models
- 📊 **Real-time Data Processing**: Live stock prices and trading data via Kiwoom OpenAPI
- 🔍 **Stock Screening**: Automated stock selection based on custom conditions
- 📱 **Slack Integration**: Real-time trading signals and analysis notifications
- 📈 **Technical Analysis**: Comprehensive analysis with RSI, MACD, Bollinger Bands, and more

## 🏗️ System Architecture

```
kiwoom/
├── main.py                      # Main application orchestrator
├── kiwoom_api.py               # Kiwoom Securities API interface
├── ai_analyzer.py              # AI-powered stock analysis engine
├── technical_analyzer.py       # Technical analysis module
├── slack_notifier.py           # Slack notification system
├── config.py                   # Configuration management
├── requirements.txt            # Package dependencies
├── start.bat                   # Windows execution script
├── data/                       # Analysis data storage
└── logs/                       # Log files storage
```

## 🔧 Installation & Setup

### 1. System Requirements
- Windows 10/11 (Required for Kiwoom OpenAPI)
- Python 3.10+
- Kiwoom Securities account with OpenAPI access

### 2. Environment Setup

```bash
# Clone repository
git clone https://github.com/guru-leo-2025/stock-finder.git
cd stock-finder

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file with the following configuration:

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

## 🚀 Usage

### Running on Windows
```bash
# Run with batch file
start.bat

# Or run directly with Python
python main.py
```

### Module Usage Example

```python
from kiwoom_api import KiwoomAPI
from ai_analyzer import AIStockAnalyzer
from technical_analyzer import TechnicalAnalyzer

# Initialize Kiwoom API
kiwoom = KiwoomAPI()

# Initialize AI analyzer
ai_analyzer = AIStockAnalyzer()

# Initialize technical analyzer
tech_analyzer = TechnicalAnalyzer()

# Run stock analysis
analysis_result = await ai_analyzer.analyze_stock("005930")  # Samsung Electronics
```

## 📊 Feature Details

### AI Analysis Engine
- **Multi-Indicator Analysis**: RSI, MACD, Bollinger Bands, Moving Averages, etc.
- **AI Model Selection**: Default `gpt-4o-mini-2024-07-18` (cost-efficient)
- **Pattern Recognition**: Automated chart pattern and technical signal detection
- **Risk Assessment**: AI-based risk scoring and evaluation

#### 📝 Supported OpenAI Models
- `gpt-4o-mini-2024-07-18` (Default, cost-efficient)
- `gpt-4o` (High performance, higher cost)
- `gpt-4-turbo` (Balanced performance)
- `gpt-4` (Standard GPT-4 model)

You can change the model using the `OPENAI_MODEL` environment variable.

### Real-time Monitoring
- Live stock price tracking
- Volume surge detection
- Custom condition alerts
- Portfolio performance tracking

### Slack Integration
- Real-time trading signal notifications
- Daily/weekly performance reports
- Market open/close alerts
- Emergency situation alerts

## 🔄 Analysis Workflow

```
Stock Data Collection (Kiwoom API)
    ↓
Technical Analysis (RSI, MACD, etc.)
    ↓
AI Enhancement (OpenAI GPT Analysis)
    ↓
Combined Recommendation
    ↓
Slack Notification (Comprehensive Report)
```

## 📈 Analysis Output Example

The system provides analysis results in the following format:

```json
{
  "stock_code": "005930",
  "stock_name": "Samsung Electronics",
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

## ⚠️ Important Disclaimers

- This system is for reference purposes only. Investment decisions are user's responsibility
- Comply with Kiwoom Securities OpenAPI terms of service
- Perform thorough backtesting before live trading
- Monitor API usage limits and manage accordingly

## 🔒 Security

- API keys and sensitive information managed via environment variables
- Personal information excluded from log files
- HTTPS communication used
- Regular dependency updates recommended

## 🛠️ Development

### Running Integration Test
```bash
python integrated_analysis_example.py
```

### Configuration Validation
```bash
python config.py
```

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/guru-leo-2025/stock-finder/issues)
- **Developer**: guru.leo.2025@gmail.com

## 📄 License

This project is provided under the MIT license.

---
**⚡ Happy Trading with AI! ⚡**