"""
Configuration management for Kiwoom Trading System
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class KiwoomConfig:
    """Kiwoom API configuration"""
    user_id: str = field(default_factory=lambda: os.getenv('KIWOOM_USER_ID', ''))
    password: str = field(default_factory=lambda: os.getenv('KIWOOM_PASSWORD', ''))
    cert_password: str = field(default_factory=lambda: os.getenv('KIWOOM_CERT_PASSWORD', ''))
    screening_condition: str = field(default_factory=lambda: os.getenv('SCREENING_CONDITION_NAME', '10stars'))

@dataclass
class OpenAIConfig:
    """OpenAI API configuration"""
    api_key: str = field(default_factory=lambda: os.getenv('OPENAI_API_KEY', ''))
    model: str = field(default_factory=lambda: os.getenv('OPENAI_MODEL', 'gpt-4o-mini-2024-07-18'))
    max_tokens: int = field(default_factory=lambda: int(os.getenv('OPENAI_MAX_TOKENS', '2000')))

@dataclass
class SlackConfig:
    """Slack API configuration"""
    bot_token: str = field(default_factory=lambda: os.getenv('SLACK_BOT_TOKEN', ''))
    channel: str = field(default_factory=lambda: os.getenv('SLACK_CHANNEL', '#trading-alerts'))

# KRX API configuration removed - no longer required
# DART API configuration removed - no longer required

@dataclass
class TradingConfig:
    """Trading system configuration"""
    max_stocks: int = field(default_factory=lambda: int(os.getenv('MAX_STOCKS_TO_ANALYZE', '10')))
    trading_mode: str = field(default_factory=lambda: os.getenv('TRADING_MODE', 'TEST'))
    analysis_interval: int = field(default_factory=lambda: int(os.getenv('ANALYSIS_INTERVAL', '300')))  # 5 minutes

# n8n integration removed as requested

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    file_path: str = field(default_factory=lambda: os.getenv('LOG_FILE', 'logs/kiwoom_trading.log'))
    max_size: int = field(default_factory=lambda: int(os.getenv('LOG_MAX_SIZE', '10485760')))  # 10MB
    backup_count: int = field(default_factory=lambda: int(os.getenv('LOG_BACKUP_COUNT', '5')))

@dataclass
class AppConfig:
    """Main application configuration"""
    kiwoom: KiwoomConfig = field(default_factory=KiwoomConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
# krx: KRXConfig removed
# dart: DartConfig removed
    trading: TradingConfig = field(default_factory=TradingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    def validate(self) -> List[str]:
        """Validate configuration settings"""
        errors = []
        
        # Kiwoom validation
        if not self.kiwoom.user_id:
            errors.append("KIWOOM_USER_ID is required")
        if not self.kiwoom.password:
            errors.append("KIWOOM_PASSWORD is required")
        if not self.kiwoom.screening_condition:
            errors.append("SCREENING_CONDITION_NAME is required")
        
        # OpenAI validation
        if not self.openai.api_key or not self.openai.api_key.startswith('sk-'):
            errors.append("Valid OPENAI_API_KEY is required (must start with 'sk-')")
        
        # Slack validation
        if not self.slack.bot_token or not self.slack.bot_token.startswith('xoxb-'):
            errors.append("Valid SLACK_BOT_TOKEN is required (must start with 'xoxb-')")
        
        # Trading mode validation
        if self.trading.trading_mode not in ['TEST', 'LIVE']:
            errors.append("TRADING_MODE must be either 'TEST' or 'LIVE'")
        
        # Create directories
        log_dir = Path(self.logging.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        Path('data').mkdir(exist_ok=True)
        
        return errors
    

# Global configuration instance
config = AppConfig()

if __name__ == "__main__":
    # Configuration validation
    errors = config.validate()
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration is valid")
        print(f"📊 Trading Mode: {config.trading.trading_mode}")
        print(f"🔍 Screening Condition: {config.kiwoom.screening_condition}")
        print(f"📈 Max Stocks to Analyze: {config.trading.max_stocks}")