"""
Main application orchestrator for Kiwoom Trading System
"""
import sys
import asyncio
import logging
import signal
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import traceback
from pathlib import Path

# Configure logging before importing other modules
def setup_logging():
    """Setup logging configuration"""
    from config import config
    
    # Create logs directory
    log_dir = Path(config.logging.file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure console handler with UTF-8 encoding
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.logging.level.upper()))
    
    # Configure file handler with UTF-8 encoding
    file_handler = logging.FileHandler(config.logging.file_path, encoding='utf-8')
    file_handler.setLevel(getattr(logging, config.logging.level.upper()))
    
    # Set formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.logging.level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # Test Korean characters
    logging.info("📋 로깅 시스템 초기화 완료")

# Setup logging first
setup_logging()

# Now import other modules
import json
from config import config
from kiwoom_api import KiwoomAPI
from slack_notifier import SlackNotifier
# KRX API removed - no longer required
# DART API removed - no longer required
from technical_analyzer import TechnicalAnalyzer

class KiwoomTradingSystem:
    """Main trading system orchestrator"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.shutdown_requested = False
        
        # Initialize components based on mode
        self._initialize_components()
        
        # System state
        self.last_analysis_time = None
        self.analysis_count = 0
        self.error_count = 0
        self.analysis_completed = False  # 분석 완료 플래그
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("🚀 Kiwoom Trading System initialized")
    
    def _initialize_components(self):
        """Initialize system components based on configuration"""
        try:
            self.logger.info("🔧 Initializing system components...")
            
            # Initialize real components only - no mock mode
            self.logger.info("🏭 Initializing production components")
            self.kiwoom = KiwoomAPI()
            self.slack = SlackNotifier()
            self.technical = TechnicalAnalyzer()
            # DART API removed - no longer required
            
            self.logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize components: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    async def start(self):
        """Start the trading system"""
        try:
            self.logger.info("🚀 Starting Kiwoom Trading System")
            self.running = True
            
            # Startup notification removed - only send results
            
            # Connect to Kiwoom API
            if not await self._connect_kiwoom():
                self.logger.error("❌ Failed to connect to Kiwoom API")
                return False
            
            # Load screening conditions
            if not self.kiwoom.load_condition_list():
                self.logger.error("❌ Failed to load screening conditions")
                return False
            
            # Start main loop
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Error in main start: {e}")
            await self._send_error_notification(str(e), "System startup")
            return False
        finally:
            await self._shutdown()
    
    async def _connect_kiwoom(self) -> bool:
        """Connect to Kiwoom API"""
        try:
            self.logger.info("🔌 Connecting to Kiwoom API...")
            
            if self.kiwoom.connect():
                self.logger.info("✅ Connected to Kiwoom API successfully")
                return True
            else:
                self.logger.error("❌ Failed to connect to Kiwoom API")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error connecting to Kiwoom: {e}")
            return False
    
    async def _main_loop(self):
        """Main analysis loop"""
        self.logger.info("🔄 메인 분석 루프 시작")
        
        loop_count = 0
        
        while self.running and not self.shutdown_requested and not self.analysis_completed:
            try:
                loop_count += 1
                self.logger.info(f"🔄 루프 {loop_count} 시작")
                
                # Check if it's time to run analysis
                should_run = self._should_run_analysis()
                
                if should_run:
                    self.logger.info("🚀 분석 실행 시작")
                    success = await self._run_full_analysis()
                    
                    if success:
                        self.logger.info("✅ 10stars 분석 완료! 프로그램을 종료합니다.")
                        self.analysis_completed = True
                        break
                else:
                    self.logger.info("⏸️ 분석 조건 미충족 - 대기 중")
                
                # 분석이 완료되지 않았을 때만 대기
                if not self.analysis_completed:
                    self.logger.info("😴 30초 대기...")
                    await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"❌ 메인 루프 오류: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                await self._send_error_notification(str(e), "Main loop")
                
                # If too many errors, break the loop
                if self.error_count > 10:
                    self.logger.error("❌ 오류가 너무 많아 시스템 중지")
                    break
                
                # Wait before retrying
                self.logger.info("😴 오류 후 60초 대기...")
                await asyncio.sleep(60)
    
    def _should_run_analysis(self) -> bool:
        """Check if analysis should be run"""
        now = datetime.now()
        
        # 현재 시간 정보 로깅
        self.logger.info(f"🕐 현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')} (요일: {now.weekday()})")
        
        # 분석 간격 체크 (공통)
        if self.last_analysis_time:
            time_since_last = now - self.last_analysis_time
            min_interval = 30 if config.is_test_mode() else config.trading.analysis_interval
            
            if time_since_last < timedelta(seconds=min_interval):
                self.logger.info(f"⏳ 마지막 분석 후 {time_since_last.total_seconds():.1f}초 경과 - 최소 간격 {min_interval}초 대기 중")
                return False
        
        # 시간 제약 없이 항상 실행 가능하도록 변경
        self.logger.info("✅ 분석 실행 조건 충족 (시간 제약 없음)")
        return True
    
    def force_run_analysis(self):
        """즉시 분석 강제 실행 (디버깅용)"""
        self.logger.info("🚀 강제 분석 실행 요청")
        self.last_analysis_time = None  # 시간 제약 무시
        return True
    
    async def _run_full_analysis(self) -> bool:
        """Run comprehensive technical analysis with Kiwoom API only"""
        try:
            self.logger.info("🔍 Kiwoom API 기반 10stars 조건식 분석 시작")
            start_time = datetime.now()
            
            # Step 1: Get stocks from 10stars screening condition
            self.logger.info("📋 10stars 조건식에서 종목 검색...")
            stock_codes = self.kiwoom.get_condition_stocks("10stars")
            
            if not stock_codes:
                self.logger.warning("⚠️ 10stars 조건에서 종목을 찾을 수 없습니다")
                return False
            
            # Limit to 10 stocks
            limited_stocks = stock_codes[:10]
            self.logger.info(f"✅ 10stars 조건에서 {len(limited_stocks)}개 종목 발견")
            
            # Step 2: Get stock names and basic info with market data
            self.logger.info("📊 종목 정보 수집...")
            stock_data = self.kiwoom.get_stock_info(limited_stocks)
            
            if not stock_data:
                self.logger.warning("⚠️ 종목 정보를 가져올 수 없습니다")
                return False
            
            # Step 3: Get historical price data and perform comprehensive technical analysis
            self.logger.info("📈 종합 기술적 분석 수행...")
            technical_analysis_data = {}
            enriched_stock_data = {}
            
            for stock_code in limited_stocks:
                try:
                    self.logger.info(f"📊 {stock_code} 기술적 분석 시작...")
                    
                    # Get historical price data (100 days for comprehensive analysis)
                    price_data = self.kiwoom.get_stock_chart_data(stock_code, period="D", count=100)
                    
                    if not price_data.empty:
                        # Perform comprehensive technical analysis
                        analysis = self.technical.analyze_stock(stock_code, price_data)
                        technical_analysis_data[stock_code] = analysis
                        
                        # Enrich stock data with technical indicators and real data
                        stock_info = stock_data.get(stock_code, {})
                        
                        # Ensure we use real technical analysis data with detailed scores
                        enriched_info = {
                            **stock_info,  # This includes real price, volume, market_cap from Kiwoom API
                            'technical_score': analysis.get('technical_score', 50),  # Real technical score
                            'detailed_scores': analysis.get('detailed_scores', {}),  # Individual indicator scores
                            'trend': analysis.get('trend', 'NEUTRAL'),
                            'rsi': analysis.get('indicators', {}).get('rsi', 'N/A'),
                            'macd_signal': analysis.get('macd_signal', 'NEUTRAL'),
                            'volume_trend': analysis.get('volume_trend', 'NORMAL'),
                            'support_level': analysis.get('support_level', 'N/A'),
                            'resistance_level': analysis.get('resistance_level', 'N/A'),
                            'recommendation': analysis.get('recommendation', 'HOLD'),
                            'buy_signals': analysis.get('buy_signals', []),
                            'risk_level': analysis.get('risk_level', '보통')
                        }
                        enriched_stock_data[stock_code] = enriched_info
                        
                        self.logger.info(f"✅ {stock_code} 기술적 분석 완료 - 점수: {analysis.get('technical_score', 'N/A')}")
                    else:
                        self.logger.warning(f"⚠️ {stock_code} 가격 데이터 없음")
                        # Add basic info even without technical analysis
                        enriched_stock_data[stock_code] = {
                            **stock_data.get(stock_code, {}),
                            'technical_score': 50,
                            'trend': 'UNKNOWN',
                            'recommendation': 'HOLD'
                        }
                        
                except Exception as e:
                    self.logger.error(f"❌ {stock_code} 기술적 분석 실패: {e}")
                    # Add basic info even on failure
                    enriched_stock_data[stock_code] = {
                        **stock_data.get(stock_code, {}),
                        'technical_score': 30,
                        'trend': 'ERROR',
                        'recommendation': 'HOLD'
                    }
                    continue
            
            self.logger.info(f"✅ 기술적 분석 완료: {len(technical_analysis_data)}/{len(limited_stocks)} 성공")
            
            # AI Analysis removed as requested
            
            # Step 5: Send comprehensive Slack notifications
            self.logger.info("📱 Slack 종합 분석 결과 전송...")
            
            # Send main technical analysis results
            try:
                # Create stock list with technical scores for ranking
                stocks_with_scores = []
                for stock_code, info in enriched_stock_data.items():
                    stock_entry = {
                        'stock_code': stock_code,
                        'stock_name': info.get('name', stock_code),
                        'current_price': info.get('current_price', 0),
                        'change_rate': info.get('change_rate', 0),
                        'volume': info.get('volume', 0),
                        'market_cap': info.get('market_cap', 0),
                        'screening_score': info.get('technical_score', 50),
                        'technical_score': info.get('technical_score', 50),  # Ensure both field names are available
                        'detailed_scores': info.get('detailed_scores', {}),  # Individual indicator scores
                        'trend': info.get('trend', 'NEUTRAL'),
                        'recommendation': info.get('recommendation', 'HOLD'),
                        'rsi': info.get('rsi', 'N/A'),
                        'macd_signal': info.get('macd_signal', 'NEUTRAL'),
                        'buy_signals': info.get('buy_signals', []),
                        'risk_level': info.get('risk_level', '보통'),
                        'market_status': info.get('market_status', '확인중'),
                        'price_type': info.get('price_type', '현재가'),
                        'is_closing_price': info.get('is_closing_price', False)
                    }
                    stocks_with_scores.append(stock_entry)
                
                # Sort by technical score
                stocks_with_scores.sort(key=lambda x: x.get('screening_score', 0), reverse=True)
                
                # Send to Slack with complete stock data
                self.logger.info(f"📱 Sending {len(stocks_with_scores)} stocks to Slack with full data")
                
                # Debug: Log first stock data to verify structure
                if stocks_with_scores:
                    sample = stocks_with_scores[0]
                    self.logger.info(f"📊 Sample stock data: {sample.get('stock_name')} - Price: {sample.get('current_price')} - Market: {sample.get('market_status')}")
                
                success = self.slack.send_stock_condition_result(
                    stocks_with_scores,  # Send complete data directly instead of simplified slack_data
                    "10stars 기술적분석", 
                    {}, 
                    technical_analysis_data
                )
                
                if success:
                    self.logger.info("✅ Slack 기술적 분석 결과 전송 완료")
                else:
                    self.logger.warning("⚠️ Slack 기술적 분석 결과 전송 실패")
                    
            except Exception as e:
                self.logger.error(f"❌ Slack 알림 실패: {e}")
            
            # AI analysis removed as requested
            
            # Step 6: Export analysis data
            self.logger.info("💾 분석 결과 데이터 내보내기...")
            
            # Create comprehensive export data
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'condition_name': '10stars',
                'stock_count': len(limited_stocks),
                'stocks': list(enriched_stock_data.values()),
                'technical_analysis': technical_analysis_data,
                'summary': {
                    'processing_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'data_sources': ['Kiwoom', 'TechnicalAnalysis'],
                    'analysis_count': self.analysis_count + 1,
                    'successful_analysis': len(technical_analysis_data),
                    'avg_technical_score': sum(s.get('technical_score', 0) for s in enriched_stock_data.values()) / len(enriched_stock_data) if enriched_stock_data else 0
                }
            }
            
            # Save comprehensive analysis data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/technical_analysis_{timestamp}.json"
            
            # Ensure data directory exists
            import os
            os.makedirs('data', exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"💾 분석 결과 저장 완료: {filename}")
            
            # Create JSON file for data backup and analysis
            stocks_json = []
            for code, info in enriched_stock_data.items():
                stocks_json.append({
                    "code": code,
                    "name": info.get('name', ''),
                    "current_price": info.get('current_price', 0),
                    "change_rate": info.get('change_rate', 0),
                    "volume": info.get('volume', 0),
                    "market_cap": info.get('market_cap', 0),
                    "technical_score": info.get('technical_score', 50),
                    "detailed_scores": info.get('detailed_scores', {}),
                    "recommendation": info.get('recommendation', 'HOLD'),
                    "risk_level": info.get('risk_level', '보통'),
                    "buy_signals": info.get('buy_signals', []),
                    "market_status": info.get('market_status', '확인중')
                })
            
            json_data = {
                "timestamp": datetime.now().isoformat(),
                "condition_name": "10stars_technical",
                "total_stocks": len(stocks_json),
                "market_analysis_summary": {
                    "avg_technical_score": sum(s.get('technical_score', 0) for s in stocks_json) / len(stocks_json) if stocks_json else 0,
                    "high_score_stocks": len([s for s in stocks_json if s.get('technical_score', 0) >= 70]),
                    "buy_recommendations": len([s for s in stocks_json if '매수' in s.get('recommendation', '')]),
                    "total_buy_signals": sum(len(s.get('buy_signals', [])) for s in stocks_json)
                },
                "stocks": stocks_json
            }
            
            json_file_path = "data/10stars_technical_analysis.json"
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 기술적 분석 JSON 파일 저장 완료: {json_file_path}")
            self.logger.info(f"📊 분석 요약 - 평균점수: {json_data['market_analysis_summary']['avg_technical_score']:.1f}, 고득점: {json_data['market_analysis_summary']['high_score_stocks']}개")
            
            # Update statistics
            self.last_analysis_time = datetime.now()
            self.analysis_count += 1
            self.error_count = 0  # Reset error count on successful analysis
            
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"🎉 Kiwoom 기술적 분석 완료! ({duration:.1f}초)")
            
            return True  # 성공 반환
            
        except Exception as e:
            self.logger.error(f"❌ 기술적 분석 중 오류: {e}")
            self.logger.error(traceback.format_exc())
            await self._send_error_notification(str(e), "Technical analysis")
            return False  # 실패 반환

    async def _send_stocks_to_slack(self, json_data: Dict[str, Any], webhook_success: bool = False, krx_data: Dict[str, Dict] = None, technical_data: Dict[str, Dict] = None) -> bool:
        """Send 10stars stocks to Slack in slack_message.txt format"""
        try:
            # Use the new send_stock_condition_result method for slack_message.txt format
            return self.slack.send_stock_condition_result(json_data, "10stars", krx_data, technical_data)
            
        except Exception as e:
            self.logger.error(f"❌ 슬랙 전송 오류: {e}")
            return False
    
    async def _send_error_notification(self, error_message: str, context: str):
        """Send error notification to Slack"""
        try:
            self.slack.send_error_alert(error_message, context)
        except Exception as e:
            self.logger.error(f"❌ Error sending error notification: {e}")
    
    async def _shutdown(self):
        """Graceful shutdown"""
        try:
            self.logger.info("🔽 Shutting down system...")
            self.running = False
            
            # Disconnect from APIs
            if hasattr(self, 'kiwoom') and hasattr(self.kiwoom, 'disconnect'):
                self.kiwoom.disconnect()
            
            self.logger.info("✅ System shutdown completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")

async def main():
    """Main entry point"""
    try:
        # Validate configuration
        errors = config.validate()
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return 1
        
        print("✅ Configuration validated")
        print(f"🔧 Trading Mode: {config.trading.trading_mode}")
        print(f"🔍 Screening Condition: {config.kiwoom.screening_condition}")
        print(f"📊 Max Stocks: {config.trading.max_stocks}")
        print()
        
        # Create and start system
        system = KiwoomTradingSystem()
        await system.start()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Shutdown requested by user")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    # Check Python version and architecture
    import platform
    
    if platform.architecture()[0] != '32bit':
        print("⚠️ Warning: 32-bit Python is recommended for Kiwoom API")
    
    if platform.system() != 'Windows':
        print("⚠️ Warning: Windows OS is required for Kiwoom API")
    
    # Run the main application
    exit_code = asyncio.run(main())