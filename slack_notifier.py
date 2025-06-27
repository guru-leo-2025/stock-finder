"""
Slack notification system for trading alerts and analysis results
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import config

class SlackNotifier:
    """Slack notification system for trading alerts"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize Slack client
        try:
            self.client = WebClient(token=config.slack.bot_token)
            self.channel = config.slack.channel
            
            # Test connection
            self._test_connection()
            self.logger.info("✅ Slack client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Slack client: {e}")
            self.client = None
    
    def _test_connection(self):
        """Test Slack API connection"""
        try:
            response = self.client.auth_test()
            if response["ok"]:
                self.logger.info(f"✅ Slack connection test successful. Bot: {response['user']}")
            else:
                raise Exception("Auth test failed")
        except SlackApiError as e:
            self.logger.error(f"❌ Slack connection test failed: {e}")
            raise
    
    def send_stock_analysis(self, stock_analyses: Dict[str, Dict], market_data: Dict[str, Dict] = None) -> bool:
        """Send individual stock analysis results"""
        if not self.client:
            self.logger.error("❌ Slack client not initialized")
            return False
        
        try:
            self.logger.info(f"📤 Sending stock analysis for {len(stock_analyses)} stocks to Slack")
            
            # Create analysis summary
            blocks = self._create_analysis_blocks(stock_analyses, market_data)
            
            # Send message
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text="🔍 AI 주식 분석 결과"  # Fallback text
            )
            
            if response["ok"]:
                self.logger.info("✅ Stock analysis sent to Slack successfully")
                return True
            else:
                self.logger.error("❌ Failed to send stock analysis to Slack")
                return False
                
        except SlackApiError as e:
            self.logger.error(f"❌ Slack API error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error sending stock analysis: {e}")
            return False
    
    def send_portfolio_analysis(self, portfolio_analysis: Dict[str, Any]) -> bool:
        """Send portfolio-level analysis"""
        if not self.client or not portfolio_analysis:
            return False
        
        try:
            self.logger.info("📤 Sending portfolio analysis to Slack")
            
            blocks = self._create_portfolio_blocks(portfolio_analysis)
            
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text="📊 포트폴리오 분석 결과"
            )
            
            if response["ok"]:
                self.logger.info("✅ Portfolio analysis sent to Slack successfully")
                return True
            else:
                self.logger.error("❌ Failed to send portfolio analysis to Slack")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error sending portfolio analysis: {e}")
            return False
    
    def send_market_sentiment(self, sentiment_analysis: Dict[str, Any]) -> bool:
        """Send market sentiment analysis"""
        if not self.client or not sentiment_analysis:
            return False
        
        try:
            self.logger.info("📤 Sending market sentiment to Slack")
            
            blocks = self._create_sentiment_blocks(sentiment_analysis)
            
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text="🌡️ 시장 심리 분석"
            )
            
            if response["ok"]:
                self.logger.info("✅ Market sentiment sent to Slack successfully")
                return True
            else:
                self.logger.error("❌ Failed to send market sentiment to Slack")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error sending market sentiment: {e}")
            return False
    
    def send_error_alert(self, error_message: str, context: str = "") -> bool:
        """Send error alert to Slack"""
        if not self.client:
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 시스템 오류 알림"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*시간:*\n{timestamp}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*컨텍스트:*\n{context}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*오류 메시지:*\n```{error_message}```"
                    }
                }
            ]
            
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=f"🚨 시스템 오류: {error_message}"
            )
            
            return response["ok"]
            
        except Exception as e:
            self.logger.error(f"❌ Error sending error alert: {e}")
            return False
    
    def _create_analysis_blocks(self, stock_analyses: Dict[str, Dict], market_data: Dict[str, Dict] = None) -> List[Dict]:
        """Create Slack blocks for stock analysis"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔍 AI 주식 분석 결과"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 분석 종목: {len(stock_analyses)}개"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
        
        # Add individual stock analyses
        for stock_code, analysis in stock_analyses.items():
            stock_name = market_data.get(stock_code, {}).get('name', '') if market_data else ''
            
            # Recommendation emoji
            rec_emoji = {
                'BUY': '🟢',
                'SELL': '🔴', 
                'HOLD': '🟡'
            }.get(analysis.get('recommendation', 'HOLD'), '🟡')
            
            # Confidence bar
            confidence = analysis.get('confidence', 0.5)
            confidence_bar = '█' * int(confidence * 10) + '░' * (10 - int(confidence * 10))
            
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{rec_emoji} {stock_name} ({stock_code})*\n*추천:* {analysis.get('recommendation', 'N/A')} | *신뢰도:* {confidence:.1%}\n`{confidence_bar}`"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*목표가:* {analysis.get('target_price', 'N/A'):,}원" if analysis.get('target_price') else "*목표가:* 미제시"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*투자기간:* {analysis.get('investment_horizon', 'N/A')}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*분석 요약:*\n{analysis.get('reasoning', 'N/A')[:200]}..."
                    }
                }
            ])
            
            # Add key factors if available
            if analysis.get('key_factors'):
                factors_text = '\n'.join([f"• {factor}" for factor in analysis['key_factors'][:3]])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*주요 요인:*\n{factors_text}"
                    }
                })
            
            blocks.append({"type": "divider"})
        
        # Add summary
        buy_count = len([a for a in stock_analyses.values() if a.get('recommendation') == 'BUY'])
        sell_count = len([a for a in stock_analyses.values() if a.get('recommendation') == 'SELL'])
        hold_count = len([a for a in stock_analyses.values() if a.get('recommendation') == 'HOLD'])
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📊 분석 요약*\n🟢 매수: {buy_count}개 | 🔴 매도: {sell_count}개 | 🟡 보유: {hold_count}개"
            }
        })
        
        return blocks
    
    def _create_portfolio_blocks(self, portfolio_analysis: Dict[str, Any]) -> List[Dict]:
        """Create Slack blocks for portfolio analysis"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 포트폴리오 분석"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*포트폴리오 점수:* {portfolio_analysis.get('portfolio_score', 'N/A')}/10"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*리스크 수준:* {portfolio_analysis.get('risk_level', 'N/A')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*분산 점수:* {portfolio_analysis.get('diversification_score', 'N/A')}/10"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*시장 전망:* {portfolio_analysis.get('market_outlook', 'N/A')}"
                    }
                ]
            }
        ]
        
        # Add recommendations
        if portfolio_analysis.get('recommendations'):
            rec_text = '\n'.join([f"• {rec}" for rec in portfolio_analysis['recommendations'][:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*💡 추천사항:*\n{rec_text}"
                }
            })
        
        # Add sector analysis
        if portfolio_analysis.get('sector_analysis'):
            sector_text = '\n'.join([f"• {sector}: {pct}%" for sector, pct in portfolio_analysis['sector_analysis'].items()])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🏭 섹터 분포:*\n{sector_text}"
                }
            })
        
        return blocks
    
    def _create_sentiment_blocks(self, sentiment_analysis: Dict[str, Any]) -> List[Dict]:
        """Create Slack blocks for market sentiment"""
        sentiment_score = sentiment_analysis.get('sentiment_score', 0)
        
        # Sentiment emoji and description
        if sentiment_score > 0.3:
            sentiment_emoji = "🟢"
            sentiment_desc = "낙관적"
        elif sentiment_score > -0.3:
            sentiment_emoji = "🟡"
            sentiment_desc = "중립적"
        else:
            sentiment_emoji = "🔴"
            sentiment_desc = "비관적"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🌡️ 시장 심리 분석"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*시장 심리:* {sentiment_emoji} {sentiment_desc}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*심리 점수:* {sentiment_score:.2f} (-1 ~ +1)"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*시장 전망:*\n{sentiment_analysis.get('market_outlook', 'N/A')}"
                }
            }
        ]
        
        # Add key factors
        if sentiment_analysis.get('key_factors'):
            factors_text = '\n'.join([f"• {factor}" for factor in sentiment_analysis['key_factors'][:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔑 주요 요인:*\n{factors_text}"
                }
            })
        
        # Add risks and opportunities
        if sentiment_analysis.get('risks') or sentiment_analysis.get('opportunities'):
            fields = []
            
            if sentiment_analysis.get('risks'):
                risks_text = '\n'.join([f"• {risk}" for risk in sentiment_analysis['risks'][:3]])
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*⚠️ 주요 리스크:*\n{risks_text}"
                })
            
            if sentiment_analysis.get('opportunities'):
                opps_text = '\n'.join([f"• {opp}" for opp in sentiment_analysis['opportunities'][:3]])
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*💡 기회 요인:*\n{opps_text}"
                })
            
            blocks.append({
                "type": "section",
                "fields": fields
            })
        
        # Add recommended strategy
        if sentiment_analysis.get('recommended_strategy'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🎯 권장 전략:*\n{sentiment_analysis['recommended_strategy']}"
                }
            })
        
        return blocks
    
    def send_message(self, message: str) -> bool:
        """Send simple message to Slack"""
        if not self.client:
            self.logger.error("❌ Slack client not initialized")
            return False
        
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message
            )
            
            if response["ok"]:
                self.logger.info("✅ Message sent to Slack successfully")
                return True
            else:
                self.logger.error("❌ Failed to send message to Slack")
                return False
                
        except SlackApiError as e:
            self.logger.error(f"❌ Slack API error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error sending message: {e}")
            return False
    
    def send_system_status(self, status: Dict[str, Any]) -> bool:
        """Send system status update"""
        if not self.client:
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            status_emoji = "🟢" if status.get('healthy', True) else "🔴"
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{status_emoji} 시스템 상태"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*상태:* {status.get('status', 'Unknown')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*시간:* {timestamp}"
                        }
                    ]
                }
            ]
            
            if status.get('message'):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*메시지:*\n{status['message']}"
                    }
                })
            
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=f"시스템 상태: {status.get('status', 'Unknown')}"
            )
            
            return response["ok"]
            
        except Exception as e:
            self.logger.error(f"❌ Error sending system status: {e}")
            return False

class MockSlackNotifier:
    """Mock Slack notifier for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("🧪 Using Mock Slack Notifier (Test Mode)")
    
    def send_stock_analysis(self, stock_analyses: Dict[str, Dict], market_data: Dict[str, Dict] = None) -> bool:
        self.logger.info(f"🧪 Mock: Would send stock analysis for {len(stock_analyses)} stocks")
        return True
    
    def send_portfolio_analysis(self, portfolio_analysis: Dict[str, Any]) -> bool:
        self.logger.info("🧪 Mock: Would send portfolio analysis")
        return True
    
    def send_market_sentiment(self, sentiment_analysis: Dict[str, Any]) -> bool:
        self.logger.info("🧪 Mock: Would send market sentiment")
        return True
    
    def send_error_alert(self, error_message: str, context: str = "") -> bool:
        self.logger.info(f"🧪 Mock: Would send error alert: {error_message}")
        return True
    
    def send_system_status(self, status: Dict[str, Any]) -> bool:
        self.logger.info(f"🧪 Mock: Would send system status: {status.get('status', 'Unknown')}")
        return True
    
    def send_message(self, message: str) -> bool:
        self.logger.info(f"🧪 Mock: Would send message: {message[:100]}...")
        return True