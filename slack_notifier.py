"""
Slack notification system using slack_block_builder.py formatting patterns
Creates messages in the same style and structure as slack_block_builder.py
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import config


class SlackBlockBuilder:
    """Slack Block Kit UI 컴포넌트 생성기 (slack_block_builder.py와 동일한 패턴)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)  # 이 줄 추가
        pass
    
    @staticmethod
    def format_currency(amount):
        """금액을 읽기 쉬운 형태로 포맷팅"""
        if amount == 'N/A' or amount is None:
            return 'N/A'
        
        try:
            amount = float(amount)
            if amount >= 1000000000000:  # 조 단위
                return f"{amount/1000000000000:.1f}조원"
            elif amount >= 100000000:  # 억 단위
                return f"{amount/100000000:.0f}억원"
            elif amount >= 10000:  # 만 단위
                return f"{amount/10000:.0f}만원"
            else:
                return f"{amount:,.0f}원"
        except (ValueError, TypeError):
            return str(amount)
    
    @staticmethod
    def format_percentage(value, decimal_places=1):
        """퍼센트 포맷팅"""
        if value == 'N/A' or value is None:
            return 'N/A'
        
        try:
            return f"{float(value):.{decimal_places}f}%"
        except (ValueError, TypeError):
            return str(value)
    
    @staticmethod
    def get_trend_emoji(value, threshold=0):
        """트렌드 이모지 반환"""
        if value == 'N/A' or value is None:
            return '➡️'
        
        try:
            value = float(value)
            if value > threshold:
                return '📈'
            elif value < threshold:
                return '📉'
            else:
                return '➡️'
        except:
            return '➡️'
    
    @staticmethod
    def get_performance_color(value, good_threshold=10, bad_threshold=0):
        """성과에 따른 색상 반환"""
        if value == 'N/A' or value is None:
            return None
        
        try:
            value = float(value)
            if value >= good_threshold:
                return "good"  # 녹색
            elif value <= bad_threshold:
                return "danger"  # 빨간색
            else:
                return "warning"  # 노란색
        except:
            return None
    
    def create_header_block(self, title, emoji="📊"):
        """헤더 블록 생성"""
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {title}"
            }
        }
    
    def create_divider_block(self):
        """구분선 블록 생성"""
        return {"type": "divider"}
    
    def create_context_block(self, elements):
        """컨텍스트 블록 생성"""
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": element
                } for element in elements
            ]
        }
    
    def create_section_with_fields(self, title, fields):
        """필드가 있는 섹션 블록 생성"""
        block = {
            "type": "section",
            "fields": []
        }
        
        if title:
            block["text"] = {
                "type": "mrkdwn",
                "text": f"*{title}*"
            }
        
        for field in fields:
            block["fields"].append({
                "type": "mrkdwn",
                "text": field
            })
        
        return block
    
    def create_action_buttons(self, buttons):
        """액션 버튼 블록 생성"""
        elements = []
        
        for button in buttons:
            element = {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": button["text"]
                },
                "action_id": button["action_id"],
                "value": button["value"]
            }
            
            if button.get("style"):
                element["style"] = button["style"]
            
            if button.get("url"):
                element["url"] = button["url"]
            
            elements.append(element)
        
        return {
            "type": "actions",
            "elements": elements
        }
    
    def create_financial_summary_block(self, financial_data, company_name):
        """재무 요약 블록 생성"""
        revenue = self.format_currency(financial_data.get('revenue'))
        net_profit = self.format_currency(financial_data.get('net_profit'))
        operating_profit = self.format_currency(financial_data.get('operating_profit'))
        
        fields = [
            f"*매출액:* {revenue}",
            f"*순이익:* {net_profit}",
            f"*영업이익:* {operating_profit}",
            f"*총자산:* {self.format_currency(financial_data.get('total_assets'))}"
        ]
        
        return self.create_section_with_fields(f"💰 {company_name} 재무 현황", fields)
    
    def create_financial_ratios_block(self, financial_data):
        """재무비율 블록 생성"""
        roe = financial_data.get('roe')
        roa = financial_data.get('roa')
        operating_margin = financial_data.get('operating_margin')
        net_margin = financial_data.get('net_margin')
        debt_ratio = financial_data.get('debt_ratio')
        
        fields = [
            f"*ROE:* {self.format_percentage(roe)} {self.get_trend_emoji(roe, 10)}",
            f"*ROA:* {self.format_percentage(roa)} {self.get_trend_emoji(roa, 5)}",
            f"*영업이익률:* {self.format_percentage(operating_margin)} {self.get_trend_emoji(operating_margin, 5)}",
            f"*순이익률:* {self.format_percentage(net_margin)} {self.get_trend_emoji(net_margin, 3)}",
            f"*부채비율:* {self.format_percentage(debt_ratio)} {self.get_trend_emoji(-debt_ratio if isinstance(debt_ratio, (int, float)) else 0, -100)}",
            f"*유동비율:* {self.format_percentage(financial_data.get('current_ratio'))} {self.get_trend_emoji(financial_data.get('current_ratio'), 100)}"
        ]
        
        return self.create_section_with_fields("📈 주요 재무비율", fields)
    
    def create_stock_info_block(self, stock_data):
        """주식 정보 블록 생성"""
        if not stock_data:
            return None
        
        current_price = stock_data.get('current_price', 'N/A')
        change_rate = stock_data.get('change_rate', 0)
        change_amount = stock_data.get('change_amount', 0)
        volume = stock_data.get('volume', 'N/A')
        
        # 등락률에 따른 이모지
        price_emoji = "📈" if change_rate > 0 else "📉" if change_rate < 0 else "➡️"
        
        if isinstance(current_price, (int, float)) and isinstance(change_amount, (int, float)) and isinstance(change_rate, (int, float)):
            price_text = f"*현재가:* {current_price:,}원 ({change_amount:+,}원, {change_rate:+.2f}%) {price_emoji}"
        else:
            price_text = f"*현재가:* {current_price} {price_emoji}"
        
        fields = [
            price_text,
            f"*거래량:* {volume:,}주" if isinstance(volume, (int, float)) else f"*거래량:* {volume}",
            f"*업데이트:* {stock_data.get('update_time', datetime.now().strftime('%Y-%m-%d %H:%M'))}"
        ]
        
        return self.create_section_with_fields("💹 주식 정보", fields)
    
    def create_company_detail_buttons(self, stock_code, corp_code=None):
        """기업 상세 분석 버튼 생성"""
        buttons = [
            {
                "text": "📋 상세 분석",
                "action_id": "view_detail_analysis",
                "value": f"detail_{stock_code}",
                "style": "primary"
            },
            {
                "text": "📈 Chart Analysis",
                "action_id": "view_chart",
                "value": f"chart_{stock_code}",
                "url": f"https://www.tradingview.com/chart/?symbol=KRX:{stock_code}"
            },
            {
                "text": "💹 네이버 금융",
                "action_id": "view_naver_finance",
                "value": f"naver_{stock_code}",
                "url": f"https://finance.naver.com/item/main.naver?code={stock_code}"
            },
            {
                "text": "🔔 알림 설정",
                "action_id": "set_alert",
                "value": f"alert_{stock_code}"
            }
        ]
        
        return self.create_action_buttons(buttons)
    
    def create_financial_report_blocks(self, financial_data, company_name, stock_data=None):
        """완전한 재무 리포트 블록 생성"""
        blocks = []
        
        # 헤더
        blocks.append(self.create_header_block(f"{company_name} 재무 분석 리포트"))
        
        # 주식 정보 (있는 경우)
        if stock_data:
            stock_block = self.create_stock_info_block(stock_data)
            if stock_block:
                blocks.append(stock_block)
                blocks.append(self.create_divider_block())
        
        # 재무 요약
        blocks.append(self.create_financial_summary_block(financial_data, company_name))
        
        # 구분선
        blocks.append(self.create_divider_block())
        
        # 재무비율
        blocks.append(self.create_financial_ratios_block(financial_data))
        
        # 액션 버튼
        stock_code = financial_data.get('stock_code', financial_data.get('corp_code', ''))
        if stock_code:
            blocks.append(self.create_company_detail_buttons(stock_code))
        
        # 업데이트 시간
        update_time = financial_data.get('update_time', datetime.now().strftime('%Y-%m-%d %H:%M'))
        blocks.append(self.create_context_block([
            f"📅 데이터 기준: {financial_data.get('year', '2023')}년",
            f"🕐 업데이트: {update_time}",
            "📊 데이터 출처: DART, 키움증권"
        ]))
        
        return blocks
    
    def create_summary_blocks(self, companies_data):
        """여러 기업 요약 블록 생성"""
        blocks = []
        
        # 헤더
        blocks.append(self.create_header_block("📈 관심종목 재무 요약"))
        
        # 각 기업별 요약
        for i, (stock_code, data) in enumerate(companies_data.items()):
            if i > 0:
                blocks.append(self.create_divider_block())
            
            company_name = data.get('company_name', stock_code)
            
            # 기업명과 주요 지표
            roe = data.get('roe', 'N/A')
            revenue = self.format_currency(data.get('revenue'))
            net_profit = self.format_currency(data.get('net_profit'))
            
            summary_text = f"*{company_name}* ({stock_code})\n"
            summary_text += f"• 매출액: {revenue}\n"
            summary_text += f"• 순이익: {net_profit}\n"
            summary_text += f"• ROE: {self.format_percentage(roe)} {self.get_trend_emoji(roe, 10)}"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": summary_text
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "상세보기"
                    },
                    "action_id": "view_company_detail",
                    "value": f"detail_{stock_code}",
                    "style": "primary"
                }
            })
        
        # 전체 요약 정보
        blocks.append(self.create_divider_block())
        blocks.append(self.create_context_block([
            f"📊 총 {len(companies_data)}개 기업 조회",
            f"🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "💡 상세보기 버튼을 클릭하면 개별 기업 분석을 확인할 수 있습니다"
        ]))
        
        return blocks
    
    def create_top_stocks_blocks(self, stocks_data):
        """상위 종목 블록 생성 (기술적 분석 포함) - Enhanced UI Design"""
        blocks = []
        
        # Enhanced 헤더 with emoji and comprehensive title
        blocks.append(self.create_header_block("📊 10stars 종목 종합 분석", "🏆"))
        
        # Add market status message if market is closed
        if stocks_data:
            sample_stock = stocks_data[0]
            market_status = sample_stock.get('market_status', '확인중')
            
            if market_status in ['장 마감', '주말 휴장', '장 시작 전']:
                if market_status == '장 마감':
                    status_message = "🔴 *장 마감* - 아래 표시된 가격은 당일 종가입니다"
                elif market_status == '주말 휴장':
                    status_message = "⚫ *주말 휴장* - 아래 표시된 가격은 전일 종가입니다"
                elif market_status == '장 시작 전':
                    status_message = "🟡 *장 시작 전* - 아래 표시된 가격은 전일 종가입니다"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": status_message
                    }
                })
                blocks.append(self.create_divider_block())
        
        for i, stock in enumerate(stocks_data[:10]):
            if i > 0 and i % 3 == 0:  # 3개마다 구분선
                blocks.append(self.create_divider_block())
            
            # Debug: Log each stock's data
            stock_code = stock.get('stock_code', 'N/A')
            current_price = stock.get('current_price', 0)
            market_status = stock.get('market_status', '확인중')
            self.logger.info(f"📊 Processing stock {i+1}: {stock_code} - Price: {current_price} - Market: {market_status}")
            
            # Enhanced stock information with comprehensive analysis
            rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"🔹"
            company_name = stock.get('stock_name', stock.get('name', stock.get('company_name', stock.get('stock_code', ''))))
            stock_code = stock.get('stock_code', '')
            
            # Core market data
            current_price = stock.get('current_price', 0)
            change_rate = stock.get('change_rate', 0)
            volume = stock.get('volume', 0)
            
            # Technical analysis data
            technical_score = stock.get('screening_score', stock.get('technical_score', 50))
            trend = stock.get('trend', 'NEUTRAL')
            recommendation = stock.get('recommendation', 'HOLD')
            rsi = stock.get('rsi', 'N/A')
            macd_signal = stock.get('macd_signal', 'NEUTRAL')
            
            # Enhanced emoji mappings for better visual appeal
            trend_emoji = {
                'BULLISH': '🟢',
                'BEARISH': '🔴', 
                'NEUTRAL': '🟡',
                'UNKNOWN': '⚪',
                'ERROR': '⚫'
            }.get(trend, '🟡')
            
            # Comprehensive recommendation mapping
            rec_emoji_map = {
                'BUY': '🟢',
                'SELL': '🔴',
                'HOLD': '🟡',
                'STRONG_BUY': '🟢🟢',
                'STRONG_SELL': '🔴🔴',
                '적극매수': '🟢🟢',
                '매수': '🟢',
                '보유': '🟡',
                '매도고려': '🔴',
                '관망': '⚪'
            }
            rec_emoji = rec_emoji_map.get(recommendation, '🟡')
            
            # Technical score color coding
            if isinstance(technical_score, (int, float)):
                if technical_score >= 75:
                    score_emoji = '🟢'  # Green for high scores
                elif technical_score >= 60:
                    score_emoji = '🟡'  # Yellow for medium scores
                else:
                    score_emoji = '🔴'  # Red for low scores
            else:
                score_emoji = '⚪'
            
            # RSI status analysis
            rsi_status = ""
            if isinstance(rsi, (int, float)):
                if rsi > 70:
                    rsi_status = "(과매수)"
                elif rsi < 30:
                    rsi_status = "(과매도)"
                else:
                    rsi_status = "(적정)"
            
            price_emoji = self.get_trend_emoji(change_rate)
            
            # Optimized stock information layout to prevent "See More" button
            # Keep stock info concise but comprehensive
            
            # Header with rank and company name
            stock_text = f"{rank_emoji} *{company_name}* ({stock_code})"
            
            # Market status indicator
            market_status = stock.get('market_status', '확인중')
            status_emoji = {
                '정규장 거래중': '🟢',
                '장 마감': '🔴', 
                '장 시작 전': '🟡',
                '주말 휴장': '⚫',
                '상태 확인 불가': '⚪'
            }.get(market_status, '⚪')
            
            stock_text += f" {status_emoji}\n"
            
            # Price information - only show actual price data (no "조회중" messages)
            price_type = stock.get('price_type', '현재가')
            is_closing_price = stock.get('is_closing_price', False)
            
            # Display all stocks regardless of price data
            if isinstance(current_price, (int, float)):
                # Add appropriate market status indicator
                if market_status == '장 마감':
                    price_indicator = f"(📈장마감-{price_type})"
                elif market_status == '주말 휴장':
                    price_indicator = f"(⚫휴장-{price_type})"
                elif market_status == '장 시작 전':
                    price_indicator = f"(🟡장시작전-{price_type})"
                elif is_closing_price:
                    price_indicator = f"({price_type})"
                else:
                    price_indicator = ""
                
                if current_price > 0:
                    if isinstance(change_rate, (int, float)):
                        stock_text += f"현재가: {current_price:,}원 ({change_rate:+.2f}%) {price_indicator}\n"
                    else:
                        stock_text += f"💰 {current_price:,}원 {price_emoji} {price_indicator}\n"
                else:
                    # Show 0 price but indicate data unavailable
                    stock_text += f"💰 가격정보 없음 ⚪ {price_indicator}\n"
            else:
                # For non-numeric price data
                stock_text += f"💰 가격정보 오류 ⚪\n"
            
            # Key metrics in one line - only show available data
            if isinstance(volume, (int, float)) and volume > 0:
                vol_display = f"{volume:,}주"
            else:
                vol_display = "정보없음"
            
            stock_text += f"거래량: {vol_display}\n"
            
            # Technical analysis - compact format
            if isinstance(technical_score, (int, float)):
                stock_text += f"기술적 점수: {technical_score:.0f}점 | 추천: {recommendation}\n"
            else:
                stock_text += f"📈 {score_emoji}점수없음 | {rec_emoji}{recommendation}\n"
            
            # RSI and MACD - compact format
            indicators_line = ""
            if isinstance(rsi, (int, float)):
                indicators_line += f"RSI: {rsi:.0f}{rsi_status}"
            
            if macd_signal != 'NEUTRAL':
                macd_emoji = '🟢' if 'BUY' in macd_signal.upper() else '🔴' if 'SELL' in macd_signal.upper() else '🟡'
                if indicators_line:
                    indicators_line += f" | MACD:{macd_emoji}"
                else:
                    indicators_line += f"MACD:{macd_emoji}"
            
            if indicators_line:
                stock_text += f"🔍 {indicators_line}\n"
            
            # Display detailed technical indicator scores
            detailed_scores = stock.get('detailed_scores', {})
            if detailed_scores:
                score_lines = []
                
                # Key individual scores with emojis
                trend_score = detailed_scores.get('trend_score', 0)
                rsi_score = detailed_scores.get('rsi_score', 0)
                macd_score = detailed_scores.get('macd_score', 0)
                volume_score = detailed_scores.get('volume_score', 0)
                signals_score = detailed_scores.get('buy_signals_score', 0)
                
                # Format scores with color indicators
                def format_score(score, name):
                    status = "상승" if score > 10 else "양호" if score > 0 else "하락" if score < -5 else "보통"
                    return f"{name}: {score:+.0f}점({status})"
                
                # Add significant scores to display
                if abs(trend_score) >= 5:
                    score_lines.append(format_score(trend_score, "추세"))
                if abs(rsi_score) >= 5:
                    score_lines.append(format_score(rsi_score, "RSI"))
                if abs(macd_score) >= 5:
                    score_lines.append(format_score(macd_score, "MACD"))
                if volume_score >= 5:
                    score_lines.append(format_score(volume_score, "거래량"))
                if signals_score >= 10:
                    score_lines.append(format_score(signals_score, "매수신호"))
                
                if score_lines:
                    # Split into multiple lines if too many scores
                    if len(score_lines) <= 3:
                        stock_text += f"📊 {' | '.join(score_lines)}"
                    else:
                        # Split into two lines
                        line1 = ' | '.join(score_lines[:3])
                        line2 = ' | '.join(score_lines[3:])
                        stock_text += f"📊 {line1}\n📊 {line2}"
            
            # Create action buttons for each stock
            action_buttons = [
                {
                    "text": "📈 Chart Analysis",
                    "action_id": "view_technical_chart",
                    "value": f"chart_{stock_code}",
                    "url": f"https://www.tradingview.com/chart/?symbol=KRX:{stock_code}",
                    "style": "primary"
                },
                {
                    "text": "💹 네이버 금융",
                    "action_id": "view_naver_finance",
                    "value": f"naver_{stock_code}",
                    "url": f"https://finance.naver.com/item/main.naver?code={stock_code}"
                }
            ]
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": stock_text
                }
            })
            
            # Add action buttons
            blocks.append(self.create_action_buttons(action_buttons))
        
        # Enhanced summary analysis section based on readme.txt
        blocks.append(self.create_divider_block())
        
        # Calculate summary statistics
        total_stocks = len(stocks_data)
        if total_stocks > 0:
            # Define recommendation emoji mapping for summary
            rec_emoji_map = {
                'BUY': '🟢',
                'SELL': '🔴',
                'HOLD': '🟡',
                'STRONG_BUY': '🟢🟢',
                'STRONG_SELL': '🔴🔴',
                '적극매수': '🟢🟢',
                '매수': '🟢',
                '보유': '🟡',
                '매도고려': '🔴',
                '관망': '⚪'
            }
            # Calculate average technical score
            avg_score = sum(stock.get('screening_score', stock.get('technical_score', 50)) 
                          for stock in stocks_data if isinstance(stock.get('screening_score', stock.get('technical_score', 50)), (int, float))) / total_stocks
            
            # Count recommendations
            recommendations = {}
            risk_levels = {'낮음': 0, '보통': 0, '높음': 0}
            buy_signals = []
            
            for stock in stocks_data:
                rec = stock.get('recommendation', 'HOLD')
                recommendations[rec] = recommendations.get(rec, 0) + 1
                
                risk = stock.get('risk_level', '보통')
                if risk in risk_levels:
                    risk_levels[risk] += 1
                
                # Collect buy signals
                signals = stock.get('buy_signals', [])
                buy_signals.extend(signals)
            
            # Count signal frequency
            signal_counts = {}
            for signal in buy_signals:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
            # Market sentiment based on scores
            if avg_score >= 70:
                market_sentiment = "강세"
                sentiment_emoji = "🟢"
            elif avg_score >= 60:
                market_sentiment = "중립"
                sentiment_emoji = "🟡"
            else:
                market_sentiment = "약세"
                sentiment_emoji = "🔴"
            
            # Create comprehensive analysis summary
            summary_text = f"📊 **기술적 분석 종합**:\n\n"
            summary_text += f"{sentiment_emoji} **시장 심리**: {market_sentiment} (평균 {avg_score:.1f}점)\n"
            
            # Recommendation distribution
            rec_summary = []
            for rec, count in recommendations.items():
                rec_emoji = rec_emoji_map.get(rec, '⚪')
                rec_summary.append(f"{rec}: {count}개")
            summary_text += f"📈 **투자추천**: {' | '.join(rec_summary)}\n"
            
            # Risk distribution
            risk_summary = []
            risk_emoji_map = {'낮음': '🟢', '보통': '🟡', '높음': '🔴'}
            for risk, count in risk_levels.items():
                if count > 0:
                    risk_summary.append(f"{risk}: {count}개")
            summary_text += f"⚠️ **리스크 분포**: {' | '.join(risk_summary)}\n"
            
            # Top signals
            if signal_counts:
                top_signals = sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                signal_text = []
                for signal, count in top_signals:
                    signal_text.append(f"{signal}({count})")
                summary_text += f"🔍 **주요 신호**: {' | '.join(signal_text)}"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": summary_text
                }
            })
            
            # Technical score calculation explanation
            blocks.append(self.create_divider_block())
            
            score_explanation = "📘 **기술적 점수 계산 방법**:\n\n"
            score_explanation += "• **기본 점수**: 50점에서 시작\n"
            score_explanation += "• **매수 신호**: 각 신호당 +10~20점 (골드크로스, RSI과매도, MACD상승전환 등)\n"
            score_explanation += "• **추세 분석**: 상승추세 시 +15점\n"
            score_explanation += "• **RSI 상태**: 건전한 RSI(40-60) +10점, 회복구간 +5점, 과매수 -10점\n"
            score_explanation += "• **MACD 모멘텀**: MACD > Signal 시 +8점\n"
            score_explanation += "• **거래량 확인**: 최근 거래량 증가 시 +5점\n"
            score_explanation += "• **최종 점수**: 0-100점 범위로 조정"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": score_explanation
                }
            })
        
        # Enhanced footer with comprehensive information
        blocks.append(self.create_divider_block())
        blocks.append(self.create_context_block([
            "📊 키움증권 API 기반 실시간 기술적 분석",
            f"🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "📈 TradingView 차트 및 네이버 금융 링크 제공",
            "🔍 RSI, MACD, 이동평균선, 볼린저밴드 등 종합 분석",
            "💡 모든 데이터는 실시간 키움증권 API에서 수집됩니다"
        ]))
        
        return blocks
    
    def create_error_blocks(self, error_message, additional_info=None):
        """에러 메시지 블록 생성"""
        blocks = []
        
        blocks.append(self.create_header_block("❌ 오류 발생"))
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*오류 내용:*\n{error_message}"
            }
        })
        
        if additional_info:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*추가 정보:*\n{additional_info}"
                }
            })
        
        blocks.append(self.create_context_block([
            f"🕐 발생시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "💡 문제가 지속되면 관리자에게 문의하세요"
        ]))
        
        return blocks
    
    def create_loading_blocks(self, message="데이터를 조회하고 있습니다..."):
        """로딩 메시지 블록 생성"""
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⏳ {message}"
                }
            },
            self.create_context_block([
                "잠시만 기다려주세요. 데이터 조회 중입니다."
            ])
        ]


class SlackNotifier:
    """Slack 알림 시스템 - slack_block_builder.py와 동일한 패턴 사용"""
    
    def __init__(self):
        """Slack 클라이언트 및 Block UI 빌더 초기화"""
        self.logger = logging.getLogger(__name__)
        
        # Slack 클라이언트 초기화
        if not config.slack.bot_token:
            raise ValueError("❌ SLACK_BOT_TOKEN이 필요합니다. .env 파일에 설정해주세요")
        
        self.client = WebClient(token=config.slack.bot_token)
        self.channel = config.slack.channel
        self.block_builder = SlackBlockBuilder()
        
        self.logger.info(f"✅ Slack 알림 시스템 초기화 완료: {self.channel}")
    
    def send_message_with_blocks(self, blocks: List[Dict], fallback_text: str = "주식 분석 리포트") -> bool:
        """
        Block UI 컴포넌트로 Slack 메시지 전송
        
        Args:
            blocks: Slack 블록 컴포넌트 리스트
            fallback_text: 알림용 대체 텍스트
            
        Returns:
            bool: 전송 성공 여부
        """
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=fallback_text,
                username="Stock Analyzer Bot",
                icon_emoji=":chart_with_upwards_trend:"
            )
            
            if response["ok"]:
                self.logger.info(f"✅ Slack 메시지 전송 성공: {self.channel}")
                return True
            else:
                self.logger.error(f"❌ Slack API 오류: {response.get('error', '알 수 없는 오류')}")
                return False
                
        except SlackApiError as e:
            self.logger.error(f"❌ Slack API 오류: {e.response['error']}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Slack 메시지 전송 실패: {e}")
            return False
    
    def send_stock_condition_result(self, stocks_data, condition_name: str, krx_data: Dict = None, technical_data: Dict = None) -> bool:
        """종목 조건 검색 결과 전송"""
        try:
            self.logger.info(f"📱 종목 조건 검색 결과 전송: {condition_name}")
            
            # Handle different data formats
            if isinstance(stocks_data, list):
                # Direct list of complete stock data from main.py
                self.logger.info(f"📊 Received list with {len(stocks_data)} stocks")
                stocks_list = stocks_data
                
                # Debug: Log sample data structure
                if stocks_list:
                    sample = stocks_list[0]
                    self.logger.info(f"📊 Sample structure: price={sample.get('current_price')}, market={sample.get('market_status')}")
                    
            elif isinstance(stocks_data, dict) and 'stocks' in stocks_data:
                # JSON 형태의 데이터를 처리
                self.logger.info(f"📊 Processing JSON format with {len(stocks_data['stocks'])} stocks")
                stocks_list = []
                for stock in stocks_data['stocks']:
                    stock_entry = {
                        'stock_code': stock.get('code', ''),
                        'stock_name': stock.get('name', stock.get('code', '')),
                        'current_price': stock.get('current_price', 0),
                        'change_rate': stock.get('change_rate', 0),
                        'volume': stock.get('volume', 0),
                        'screening_score': stock.get('technical_score', 75),
                        'technical_score': stock.get('technical_score', 75),
                        'detailed_scores': stock.get('detailed_scores', {}),
                        'market_status': stock.get('market_status', '확인중'),
                        'price_type': stock.get('price_type', '현재가'),
                        'is_closing_price': stock.get('is_closing_price', False),
                        'trend': stock.get('trend', 'NEUTRAL'),
                        'recommendation': stock.get('recommendation', 'HOLD'),
                        'rsi': stock.get('rsi', 'N/A'),
                        'macd_signal': stock.get('macd_signal', 'NEUTRAL'),
                        'buy_signals': stock.get('buy_signals', []),
                        'risk_level': stock.get('risk_level', '보통')
                    }
                    stocks_list.append(stock_entry)
            else:
                # 직접 stocks_data가 딕셔너리인 경우
                self.logger.info(f"📊 Processing dictionary format with {len(stocks_data)} stocks")
                stocks_list = []
                for stock_code, stock_info in stocks_data.items():
                    stock_entry = {
                        'stock_code': stock_code,
                        'stock_name': stock_info.get('name', stock_code),
                        'current_price': stock_info.get('current_price', 0),
                        'change_rate': stock_info.get('change_rate', 0),
                        'volume': stock_info.get('volume', 0),
                        'screening_score': stock_info.get('screening_score', 75),
                        'technical_score': stock_info.get('technical_score', 75),
                        'detailed_scores': stock_info.get('detailed_scores', {}),
                        'market_status': stock_info.get('market_status', '확인중'),
                        'price_type': stock_info.get('price_type', '현재가'),
                        'is_closing_price': stock_info.get('is_closing_price', False),
                        'trend': stock_info.get('trend', 'NEUTRAL'),
                        'recommendation': stock_info.get('recommendation', 'HOLD'),
                        'rsi': stock_info.get('rsi', 'N/A'),
                        'macd_signal': stock_info.get('macd_signal', 'NEUTRAL'),
                        'buy_signals': stock_info.get('buy_signals', []),
                        'risk_level': stock_info.get('risk_level', '보통')
                    }
                    stocks_list.append(stock_entry)
            
            # 점수순으로 정렬
            stocks_list.sort(key=lambda x: x.get('screening_score', 0), reverse=True)
            
            # Debug: Log data before sending to blocks
            if stocks_list:
                self.logger.info(f"📊 Generating blocks for {len(stocks_list)} stocks")
                sample = stocks_list[0]
                self.logger.info(f"📊 Block generation sample: {sample.get('stock_name')} - Price: {sample.get('current_price')} - Status: {sample.get('market_status')}")
            
            # 블록 생성 - Use block_builder which contains the method
            blocks = self.block_builder.create_top_stocks_blocks(stocks_list)
            
            # 조건별 헤더 추가
            header_block = self.block_builder.create_header_block(
                f"{condition_name} 조건식 검색 결과", 
                "🎯"
            )
            blocks.insert(0, header_block)
            
            # 요약 정보 추가
            summary_context = self.block_builder.create_context_block([
                f"📊 검색조건: {condition_name}",
                f"🔍 발견종목: {len(stocks_list)}개",
                f"🕐 검색시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            ])
            blocks.insert(1, summary_context)
            blocks.insert(2, self.block_builder.create_divider_block())
            
            # 메시지 전송
            return self.send_message_with_blocks(
                blocks=blocks,
                fallback_text=f"{condition_name} 조건식에서 {len(stocks_list)}개 종목이 검색되었습니다."
            )
            
        except Exception as e:
            self.logger.error(f"❌ 종목 조건 검색 결과 전송 오류: {e}")
            return False
    
    def send_financial_analysis(self, financial_data: Dict[str, Dict], stock_data: Dict[str, Dict] = None) -> bool:
        """재무 분석 결과 전송"""
        try:
            self.logger.info("📱 재무 분석 리포트 전송")
            
            if not financial_data:
                return self._send_no_data_message("재무 분석 데이터가 없습니다.")
            
            # 여러 기업 요약 블록 생성
            blocks = self.block_builder.create_summary_blocks(financial_data)
            
            # 메시지 전송
            return self.send_message_with_blocks(
                blocks=blocks,
                fallback_text=f"재무 분석 리포트 - {len(financial_data)}개 기업"
            )
            
        except Exception as e:
            self.logger.error(f"❌ 재무 분석 전송 오류: {e}")
            return False
    
    
    def send_error_alert(self, error_message: str, context: str = "System Error") -> bool:
        """오류 알림 전송"""
        try:
            self.logger.info(f"📱 오류 알림 전송: {context}")
            
            # 오류 블록 생성
            blocks = self.block_builder.create_error_blocks(
                error_message=error_message,
                additional_info=f"발생 위치: {context}"
            )
            
            # 메시지 전송
            return self.send_message_with_blocks(
                blocks=blocks,
                fallback_text=f"시스템 오류 발생: {context}"
            )
            
        except Exception as e:
            self.logger.error(f"❌ 오류 알림 전송 실패: {e}")
            return False
    
    def _send_no_data_message(self, message: str) -> bool:
        """데이터 없음 메시지 전송"""
        blocks = [
            self.block_builder.create_header_block("📭 데이터 없음", "ℹ️"),
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*알림:* {message}"
                }
            },
            self.block_builder.create_context_block([
                f"🕐 확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "💡 나중에 다시 시도해보세요"
            ])
        ]
        
        return self.send_message_with_blocks(
            blocks=blocks,
            fallback_text=message
        )
    
    def send_ai_enhanced_analysis(self, ai_analysis_results: Dict[str, Dict], condition_name: str = "AI 강화 분석") -> bool:
        """AI가 강화된 기술적 분석 결과를 Slack으로 전송"""
        try:
            self.logger.info(f"📱 AI 강화 분석 결과 전송: {condition_name}")
            
            if not ai_analysis_results:
                return self._send_no_data_message("AI 분석 결과가 없습니다.")
            
            # AI 분석 결과를 Slack 블록으로 변환
            blocks = self._create_ai_enhanced_analysis_blocks(ai_analysis_results, condition_name)
            
            # 메시지 전송
            return self.send_message_with_blocks(
                blocks=blocks,
                fallback_text=f"AI 강화 분석 결과 - {len(ai_analysis_results)}개 종목"
            )
            
        except Exception as e:
            self.logger.error(f"❌ AI 강화 분석 결과 전송 오류: {e}")
            return False
    
    def _create_ai_enhanced_analysis_blocks(self, ai_results: Dict[str, Dict], condition_name: str) -> List[Dict]:
        """AI 강화 분석 결과를 위한 Slack 블록 생성"""
        blocks = []
        
        # 헤더
        blocks.append(self.block_builder.create_header_block(f"🤖 {condition_name} - AI 강화 분석", "🧠"))
        
        # 요약 정보
        total_stocks = len(ai_results)
        ai_recommendations = {'BUY': 0, 'SELL': 0, 'HOLD': 0, '적극매수': 0, '관망': 0}
        high_confidence_count = 0
        
        for stock_code, analysis in ai_results.items():
            final_rec = analysis.get('final_recommendation', analysis.get('recommendation', 'HOLD'))
            if final_rec in ai_recommendations:
                ai_recommendations[final_rec] += 1
            
            ai_analysis = analysis.get('ai_analysis', {})
            if ai_analysis.get('ai_confidence', 0) > 0.7:
                high_confidence_count += 1
        
        summary_text = f"📊 **AI 분석 요약**:\n"
        summary_text += f"• 총 분석 종목: {total_stocks}개\n"
        summary_text += f"• 고신뢰도 분석: {high_confidence_count}개 (70% 이상)\n"
        summary_text += f"• 적극매수: {ai_recommendations.get('적극매수', 0)}개\n"
        summary_text += f"• 매수(BUY): {ai_recommendations.get('BUY', 0)}개\n"
        summary_text += f"• 보유(HOLD): {ai_recommendations.get('HOLD', 0)}개\n"
        summary_text += f"• 관망: {ai_recommendations.get('관망', 0)}개"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": summary_text
            }
        })
        
        blocks.append(self.block_builder.create_divider_block())
        
        # 개별 종목 분석 (상위 10개)
        sorted_stocks = sorted(ai_results.items(), 
                              key=lambda x: x[1].get('technical_score', 0), 
                              reverse=True)
        
        for i, (stock_code, analysis) in enumerate(sorted_stocks[:10]):
            if i > 0 and i % 3 == 0:
                blocks.append(self.block_builder.create_divider_block())
            
            stock_name = analysis.get('stock_name', stock_code)
            technical_score = analysis.get('technical_score', 50)
            recommendation = analysis.get('final_recommendation', analysis.get('recommendation', 'HOLD'))
            
            # 기본 정보 추출
            market_data = analysis.get('market_data', {})
            current_price = market_data.get('current_price', 0)
            change_rate = analysis.get('change_rate', 0)
            volume = analysis.get('volume', market_data.get('volume', 0))
            
            # RSI 정보
            indicators = analysis.get('indicators', {})
            rsi = indicators.get('rsi', 'N/A')
            rsi_status = "과매수" if isinstance(rsi, (int, float)) and rsi > 70 else "과매도" if isinstance(rsi, (int, float)) and rsi < 30 else "적정"
            
            # 세부 점수 정보
            detailed_scores = analysis.get('detailed_scores', {})
            trend_score = detailed_scores.get('trend_score', 0)
            rsi_score = detailed_scores.get('rsi_score', 0)
            macd_score = detailed_scores.get('macd_score', 0)
            
            # 이모지 매핑
            rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}️⃣"
            
            rec_emoji = {
                'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡',
                '적극매수': '🟢', '매수': '🟢', '보유': '🟡', '관망': '⚪'
            }.get(recommendation, '🟡')
            
            # 간결한 스타일로 구성
            stock_text = f"{rank_emoji} {stock_name} ({stock_code}) {rec_emoji}\n"
            
            # 현재가 정보
            if isinstance(current_price, (int, float)) and current_price > 0:
                if isinstance(change_rate, (int, float)) and change_rate != 0:
                    change_sign = "+" if change_rate > 0 else ""
                    stock_text += f"현재가: {current_price:,}원 ({change_sign}{change_rate:.2f}%)\n"
                else:
                    stock_text += f"현재가: {current_price:,}원\n"
            
            # 거래량
            if isinstance(volume, (int, float)) and volume > 0:
                stock_text += f"거래량: {volume:,}주\n"
            
            # 기술적 점수와 추천
            stock_text += f"기술적 점수: {technical_score:.0f}점 | 추천: {recommendation}\n"
            
            # RSI 정보
            if isinstance(rsi, (int, float)):
                stock_text += f"🔍 RSI: {rsi:.0f}({rsi_status})\n"
            
            # 세부 점수 (의미있는 것만)
            score_parts = []
            if abs(trend_score) >= 5:
                trend_status = "상승" if trend_score > 0 else "하락"
                score_parts.append(f"추세: {trend_score:+.0f}점({trend_status})")
            if abs(rsi_score) >= 5:
                rsi_trend = "상승" if rsi_score > 0 else "하락" if rsi_score < -5 else "보통"
                score_parts.append(f"RSI: {rsi_score:+.0f}점({rsi_trend})")
            if abs(macd_score) >= 5:
                macd_trend = "상승" if macd_score > 0 else "하락" if macd_score < -5 else "보통"
                score_parts.append(f"MACD: {macd_score:+.0f}점({macd_trend})")
            
            if score_parts:
                stock_text += f"📊 {' | '.join(score_parts[:3])}\n"
            
            # AI 분석 (간결하게)
            ai_analysis = analysis.get('ai_analysis', {})
            if ai_analysis and ai_analysis.get('ai_reasoning'):
                ai_reasoning = ai_analysis.get('ai_reasoning', '')
                sentences = self._format_ai_analysis_sentences(ai_reasoning)
                if sentences and len(sentences) > 0:
                    # 첫 번째 문장만 표시
                    first_sentence = sentences[0]
                    if len(first_sentence) > 80:
                        first_sentence = first_sentence[:80] + "..."
                    stock_text += f"🤖 AI분석: {first_sentence}"
                else:
                    short_ai = ai_reasoning[:60] + "..." if len(ai_reasoning) > 60 else ai_reasoning
                    stock_text += f"🤖 AI분석: {short_ai}"
            else:
                stock_text += f"🤖 AI분석: 분석 정보 없음"
            
            # 액션 버튼
            action_buttons = [
                {
                    "text": "📈 차트보기",
                    "action_id": "view_chart",
                    "value": f"chart_{stock_code}",
                    "url": f"https://www.tradingview.com/chart/?symbol=KRX:{stock_code}",
                    "style": "primary"
                },
                {
                    "text": "💹 네이버금융",
                    "action_id": "view_naver",
                    "value": f"naver_{stock_code}",
                    "url": f"https://finance.naver.com/item/main.naver?code={stock_code}"
                }
            ]
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": stock_text
                }
            })
            
            blocks.append(self.block_builder.create_action_buttons(action_buttons))
        
        # AI 분석 방법론 설명
        blocks.append(self.block_builder.create_divider_block())
        
        methodology_text = "🧠 **AI 분석 방법론**:\n\n"
        methodology_text += "• **기술적 분석 + AI 융합**: 전통적 기술적 지표를 AI가 해석\n"
        methodology_text += "• **패턴 인식**: 차트 패턴과 시장 심리를 AI가 종합 분석\n"
        methodology_text += "• **신뢰도 기반 추천**: AI 신뢰도에 따른 가중 추천\n"
        methodology_text += "• **리스크 평가**: 변동성과 시장 상황을 고려한 위험도 평가\n"
        methodology_text += "• **목표가 산정**: 지지/저항선 분석을 통한 합리적 목표가 제시"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": methodology_text
            }
        })
        
        # 푸터
        blocks.append(self.block_builder.create_divider_block())
        blocks.append(self.block_builder.create_context_block([
            "🤖 OpenAI GPT-4 기반 AI 분석",
            f"📊 기술적 분석: RSI, MACD, 이동평균선, 볼린저밴드 등",
            f"🕐 분석시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "⚠️ 투자 판단의 참고자료로만 활용하세요"
        ]))
        
        return blocks
    
    def _format_ai_analysis_sentences(self, ai_reasoning: str) -> List[str]:
        """Format AI analysis reasoning into clean sentences for Slack display"""
        try:
            if not ai_reasoning or ai_reasoning.strip() == "AI 분석 정보 없음":
                return []
            
            # Split into sentences and clean up
            sentences = []
            
            # Split by common sentence endings (Korean and English)
            import re
            # Split by periods, exclamation marks, question marks
            raw_sentences = re.split(r'[.!?。！？]', ai_reasoning)
            
            for sentence in raw_sentences:
                cleaned = sentence.strip()
                # Filter out very short fragments or common filler words
                if cleaned and len(cleaned) > 15 and not cleaned.lower().startswith(('the', 'a', 'an', 'this', 'that')):
                    # Remove leading bullet points or numbers
                    cleaned = re.sub(r'^[\d\-•*\s]+', '', cleaned).strip()
                    
                    # Ensure sentence starts with capital letter (for English) or proper Korean
                    if cleaned and not cleaned[0].isupper() and cleaned[0].isalpha():
                        cleaned = cleaned[0].upper() + cleaned[1:]
                    
                    # Add period if missing
                    if cleaned and not cleaned.endswith(('.', '!', '?', '다', '음', '요')):
                        cleaned += '.'
                    
                    sentences.append(cleaned)
            
            # If no proper sentences found, try splitting by line breaks
            if not sentences:
                lines = ai_reasoning.split('\n')
                for line in lines:
                    cleaned = line.strip()
                    if cleaned and len(cleaned) > 15:
                        sentences.append(cleaned)
            
            # Limit to 4 sentences for better display
            return sentences[:4]
            
        except Exception as e:
            self.logger.error(f"❌ AI 분석 문장 포맷팅 실패: {e}")
            # Return the original text truncated as fallback
            return [ai_reasoning[:150] + "..." if len(ai_reasoning) > 150 else ai_reasoning]