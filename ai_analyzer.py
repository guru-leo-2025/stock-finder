"""
AI-powered stock analysis using OpenAI API
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import asyncio
import openai
from openai import OpenAI

from config import config

class AIStockAnalyzer:
    """AI-powered stock analysis using OpenAI GPT models"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        try:
            self.client = OpenAI(api_key=config.openai.api_key)
            self.model = config.openai.model
            self.max_tokens = config.openai.max_tokens
            
            # Test API connection
            self._test_connection()
            self.logger.info("✅ OpenAI API initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize OpenAI API: {e}")
            self.client = None
    
    def _test_connection(self):
        """Test OpenAI API connection"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            self.logger.info("✅ OpenAI API connection test successful")
        except Exception as e:
            self.logger.error(f"❌ OpenAI API connection test failed: {e}")
            raise
    
    def analyze_stocks_with_technical_data(self, technical_analysis_results: Dict[str, Dict]) -> Dict[str, Dict]:
        """Analyze stocks using technical analysis data and provide AI-enhanced recommendations"""
        if not self.client:
            self.logger.error("❌ OpenAI client not initialized")
            return {}
        
        analysis_results = {}
        
        try:
            self.logger.info(f"🤖 Starting AI analysis for {len(technical_analysis_results)} stocks with technical data")
            
            for stock_code, technical_data in technical_analysis_results.items():
                stock_name = technical_data.get('stock_name', stock_code)
                self.logger.info(f"🔍 AI analyzing stock: {stock_name} ({stock_code})")
                
                # Get AI analysis based on technical data
                analysis = self._get_technical_ai_analysis(stock_code, technical_data)
                
                if analysis:
                    # Combine technical analysis with AI insights
                    combined_analysis = self._combine_technical_and_ai_analysis(technical_data, analysis)
                    analysis_results[stock_code] = combined_analysis
                    self.logger.info(f"✅ AI analysis completed for {stock_name}")
                else:
                    self.logger.warning(f"⚠️ AI analysis failed for {stock_name}")
                    # Fall back to technical analysis only
                    analysis_results[stock_code] = technical_data
            
            self.logger.info(f"🤖 AI analysis completed for {len(analysis_results)} stocks")
            
        except Exception as e:
            self.logger.error(f"❌ Error in AI stock analysis: {e}")
        
        return analysis_results

    def analyze_stocks(self, stock_data: Dict[str, Dict], market_data: Dict[str, Dict] = None) -> Dict[str, Dict]:
        """Analyze stocks and provide buy/sell recommendations (original method maintained for compatibility)"""
        if not self.client:
            self.logger.error("❌ OpenAI client not initialized")
            return {}
        
        analysis_results = {}
        
        try:
            self.logger.info(f"🤖 Starting AI analysis for {len(stock_data)} stocks")
            
            for stock_code, stock_info in stock_data.items():
                self.logger.info(f"🔍 Analyzing stock: {stock_info.get('name', stock_code)}")
                
                # Prepare comprehensive data for analysis
                analysis_data = self._prepare_analysis_data(stock_code, stock_info, market_data)
                
                # Get AI analysis
                analysis = self._get_stock_analysis(analysis_data)
                
                if analysis:
                    analysis_results[stock_code] = analysis
                    self.logger.info(f"✅ Analysis completed for {stock_info.get('name', stock_code)}")
                else:
                    self.logger.warning(f"⚠️ Analysis failed for {stock_info.get('name', stock_code)}")
            
            self.logger.info(f"🤖 AI analysis completed for {len(analysis_results)} stocks")
            
        except Exception as e:
            self.logger.error(f"❌ Error in stock analysis: {e}")
        
        return analysis_results
    
    def _prepare_analysis_data(self, stock_code: str, stock_info: Dict, market_data: Dict = None) -> Dict:
        """Prepare comprehensive data for AI analysis"""
        analysis_data = {
            'stock_code': stock_code,
            'stock_info': stock_info,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add market data if available
        if market_data and stock_code in market_data:
            analysis_data['market_data'] = market_data[stock_code]
        
        return analysis_data
    
    def _get_stock_analysis(self, analysis_data: Dict) -> Optional[Dict]:
        """Get AI analysis for a single stock"""
        try:
            # Create comprehensive analysis prompt
            prompt = self._create_analysis_prompt(analysis_data)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            analysis = json.loads(content)
            
            # Add metadata
            analysis['ai_model'] = self.model
            analysis['analysis_timestamp'] = datetime.now().isoformat()
            analysis['tokens_used'] = response.usage.total_tokens
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error getting AI analysis: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI analysis"""
        return """
You are a professional Korean stock market analyst with expertise in fundamental and technical analysis.
Your task is to analyze stocks and provide buy/sell recommendations with detailed reasoning.

Guidelines:
1. Provide clear BUY, SELL, or HOLD recommendations
2. Include detailed reasoning based on financial metrics
3. Consider market conditions and sector trends  
4. Highlight key risks and opportunities
5. Provide target price if possible
6. Use Korean stock market context (KOSPI/KOSDAQ)

Response format must be JSON with these fields:
{
    "recommendation": "BUY|SELL|HOLD",
    "confidence": 0.0-1.0,
    "target_price": number or null,
    "reasoning": "detailed explanation",
    "key_factors": ["factor1", "factor2", ...],
    "risks": ["risk1", "risk2", ...],
    "opportunities": ["opp1", "opp2", ...],
    "technical_analysis": "brief technical assessment",
    "fundamental_analysis": "brief fundamental assessment",
    "sector_outlook": "sector trend analysis",
    "investment_horizon": "SHORT|MEDIUM|LONG"
}
"""
    
    def _create_analysis_prompt(self, analysis_data: Dict) -> str:
        """Create analysis prompt for specific stock"""
        stock_info = analysis_data['stock_info']
        market_data = analysis_data.get('market_data', {})
        
        prompt = f"""
주식 분석 요청:

기본 정보:
- 종목코드: {analysis_data['stock_code']}
- 종목명: {stock_info.get('name', 'N/A')}
- 현재가: {stock_info.get('current_price', 'N/A'):,}원
- 거래량: {stock_info.get('volume', 'N/A'):,}주

재무지표:
- 시가총액: {market_data.get('market_cap', 'N/A')}백만원
- PER: {market_data.get('per', 'N/A')}
- PBR: {market_data.get('pbr', 'N/A')}
- ROE: {market_data.get('roe', 'N/A')}%
- 부채비율: {market_data.get('debt_ratio', 'N/A')}%
- 배당수익률: {market_data.get('dividend_yield', 'N/A')}%

시장 정보:
- 업종: {market_data.get('sector', 'N/A')}
- 시장: {market_data.get('market', 'N/A')}
- 5일 평균거래량: {market_data.get('avg_volume_5d', 'N/A')}
- 거래량 추세: {market_data.get('volume_trend', 'N/A')}

이 종목에 대한 종합적인 투자 분석과 매수/매도/보유 추천을 해주세요.
현재 한국 증시 상황과 해당 업종의 전망도 고려해 주세요.
"""
        
        return prompt
    
    def analyze_portfolio(self, stock_analyses: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze overall portfolio and provide portfolio-level insights"""
        if not self.client or not stock_analyses:
            return {}
        
        try:
            self.logger.info("🤖 Starting portfolio-level analysis")
            
            # Prepare portfolio summary
            portfolio_summary = self._prepare_portfolio_summary(stock_analyses)
            
            # Create portfolio analysis prompt
            prompt = f"""
포트폴리오 분석 요청:

개별 종목 분석 결과:
{json.dumps(portfolio_summary, ensure_ascii=False, indent=2)}

이 포트폴리오에 대한 종합적인 분석을 해주세요:
1. 전체적인 포트폴리오 평가
2. 섹터 분산 분석
3. 리스크/수익 밸런스
4. 추천 포트폴리오 조정 사항
5. 시장 상황 대응 전략

JSON 형식으로 응답해 주세요.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a portfolio manager specializing in Korean stocks. 
                        Provide comprehensive portfolio analysis in JSON format with fields:
                        portfolio_score, risk_level, diversification_score, recommendations, 
                        sector_analysis, market_outlook, suggested_actions."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            portfolio_analysis = json.loads(response.choices[0].message.content)
            portfolio_analysis['analysis_timestamp'] = datetime.now().isoformat()
            
            self.logger.info("✅ Portfolio analysis completed")
            return portfolio_analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error in portfolio analysis: {e}")
            return {}
    
    def _prepare_portfolio_summary(self, stock_analyses: Dict[str, Dict]) -> Dict:
        """Prepare summary of individual stock analyses for portfolio analysis"""
        summary = {
            'total_stocks': len(stock_analyses),
            'recommendations': {
                'BUY': 0, 'SELL': 0, 'HOLD': 0
            },
            'sectors': {},
            'average_confidence': 0.0,
            'key_insights': []
        }
        
        total_confidence = 0
        
        for stock_code, analysis in stock_analyses.items():
            # Count recommendations
            rec = analysis.get('recommendation', 'HOLD')
            summary['recommendations'][rec] = summary['recommendations'].get(rec, 0) + 1
            
            # Track confidence
            confidence = analysis.get('confidence', 0.5)
            total_confidence += confidence
            
            # Track sectors (if available in the analysis)
            sector = analysis.get('sector', 'Unknown')
            summary['sectors'][sector] = summary['sectors'].get(sector, 0) + 1
            
            # Collect key insights
            if analysis.get('reasoning'):
                summary['key_insights'].append({
                    'stock_code': stock_code,
                    'recommendation': rec,
                    'confidence': confidence,
                    'key_reason': analysis.get('reasoning', '')[:100] + '...'
                })
        
        # Calculate average confidence
        if len(stock_analyses) > 0:
            summary['average_confidence'] = total_confidence / len(stock_analyses)
        
        return summary
    
    def _get_technical_ai_analysis(self, stock_code: str, technical_data: Dict) -> Optional[Dict]:
        """Get AI analysis based on technical analysis data"""
        try:
            self.logger.info(f"🤖 {stock_code} AI 분석 시작...")
            
            # Create enhanced technical analysis prompt
            prompt = self._create_technical_analysis_prompt(stock_code, technical_data)
            
            # Save prompt to data directory for debugging
            self._save_analysis_data(stock_code, 'prompt', prompt)
            
            # Call OpenAI API with technical data context
            self.logger.info(f"🔗 OpenAI API 호출: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_technical_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            self.logger.info(f"✅ {stock_code} OpenAI 응답 수신 완료")
            
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ {stock_code} JSON 파싱 실패: {e}")
                self.logger.error(f"Raw content: {content}")
                return None
            
            # Add metadata
            analysis['ai_model'] = self.model
            analysis['analysis_timestamp'] = datetime.now().isoformat()
            analysis['tokens_used'] = response.usage.total_tokens
            analysis['stock_code'] = stock_code
            analysis['stock_name'] = technical_data.get('stock_name', stock_code)
            
            # Save analysis result to data directory
            self._save_analysis_data(stock_code, 'ai_analysis', analysis)
            
            self.logger.info(f"✅ {stock_code} AI 분석 완료")
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ {stock_code} AI 분석 실패: {e}")
            import traceback
            self.logger.error(f"Error details: {traceback.format_exc()}")
            return None
    
    def _get_technical_system_prompt(self) -> str:
        """Get system prompt specifically for technical analysis enhancement"""
        return """
You are an expert Korean stock market technical analyst with deep knowledge of chart patterns, technical indicators, and market psychology.
Your task is to enhance technical analysis results with AI insights and provide comprehensive investment recommendations.

Guidelines:
1. Analyze the provided technical indicators (RSI, MACD, Moving Averages, Bollinger Bands, etc.)
2. Interpret chart patterns and market signals
3. Consider volume analysis and momentum indicators
4. Provide clear BUY, SELL, or HOLD recommendations with confidence levels
5. Identify key support and resistance levels
6. Assess short-term and medium-term price targets
7. Highlight potential risks and opportunities
8. Use Korean stock market context and terminology

Response format must be JSON with these fields:
{
    "ai_recommendation": "BUY|SELL|HOLD",
    "ai_confidence": 0.0-1.0,
    "ai_reasoning": "detailed AI analysis explanation",
    "target_price_range": {"low": number, "high": number},
    "stop_loss_level": number or null,
    "key_insights": ["insight1", "insight2", ...],
    "risk_factors": ["risk1", "risk2", ...],
    "catalysts": ["catalyst1", "catalyst2", ...],
    "technical_summary": "brief technical pattern summary",
    "market_context": "current market environment analysis",
    "time_horizon": "SHORT|MEDIUM|LONG",
    "volatility_assessment": "LOW|MEDIUM|HIGH"
}
"""
    
    def _create_technical_analysis_prompt(self, stock_code: str, technical_data: Dict) -> str:
        """Create detailed prompt for technical analysis AI enhancement"""
        stock_name = technical_data.get('stock_name', stock_code)
        technical_score = technical_data.get('technical_score', 50)
        recommendation = technical_data.get('recommendation', 'HOLD')
        risk_level = technical_data.get('risk_level', '보통')
        
        # Extract technical indicators
        indicators = technical_data.get('indicators', {})
        buy_signals = technical_data.get('buy_signals', [])
        detailed_scores = technical_data.get('detailed_scores', {})
        technical_summary = technical_data.get('technical_summary', {})
        market_data = technical_data.get('market_data', {})
        
        # Safe number formatting
        def safe_format_number(value, decimals=0):
            try:
                if value == 'N/A' or value is None:
                    return 'N/A'
                return f"{float(value):,.{decimals}f}"
            except:
                return str(value)
        
        def safe_format_currency(value):
            try:
                if value == 'N/A' or value is None:
                    return 'N/A'
                return f"{float(value):,.0f}원"
            except:
                return str(value)
        
        prompt = f"""
종목 기술적 분석 AI 강화 요청:

=== 기본 정보 ===
- 종목명: {stock_name}
- 종목코드: {stock_code}
- 현재가: {safe_format_currency(market_data.get('current_price'))}
- 거래량: {safe_format_number(market_data.get('volume'))}주
- 52주 최고가: {safe_format_currency(market_data.get('high_52w'))}
- 52주 최저가: {safe_format_currency(market_data.get('low_52w'))}

=== 기술적 분석 결과 ===
- 기술적 점수: {technical_score:.1f}점 (100점 만점)
- 기본 추천: {recommendation}
- 리스크 수준: {risk_level}

=== 기술적 지표 ===
- RSI: {safe_format_number(indicators.get('rsi'), 1)}
- MACD: {safe_format_number(indicators.get('macd'), 4)} (신호선: {safe_format_number(indicators.get('macd_signal'), 4)})
- 5일 이평선: {safe_format_currency(indicators.get('sma_5'))}
- 20일 이평선: {safe_format_currency(indicators.get('sma_20'))}
- 스토캐스틱 %K: {safe_format_number(indicators.get('stoch_k'), 1)}
- 스토캐스틱 %D: {safe_format_number(indicators.get('stoch_d'), 1)}

=== 매수 신호 ===
{', '.join(buy_signals) if buy_signals else '매수신호 없음'}

=== 추가 분석 정보 ===
- 가격 추세: {technical_summary.get('price_trend', '분석불가')}
- 거래량 추세: {technical_summary.get('volume_trend', '분석불가')}
- 이동평균선 배열: {technical_summary.get('moving_average_position', '분석불가')}
- 변동성 수준: {technical_summary.get('volatility', '분석불가')}
- 볼린저밴드 위치: {technical_summary.get('bollinger_position', '분석불가')}
- 모멘텀 분석: {technical_summary.get('momentum_analysis', '분석불가')}

위 데이터를 바탕으로 이 종목에 대한 상세한 투자 분석을 제공해 주세요. 
분석은 3-5개의 명확한 문장으로 구성하고, 투자자가 이해하기 쉽게 작성해 주세요.
"""
        
        return prompt
    
    def _combine_technical_and_ai_analysis(self, technical_data: Dict, ai_analysis: Dict) -> Dict:
        """Combine technical analysis results with AI insights"""
        try:
            # Start with technical analysis data
            combined = technical_data.copy()
            
            # Add AI analysis results
            combined['ai_analysis'] = ai_analysis
            
            # Create enhanced recommendation based on both analyses
            technical_rec = technical_data.get('recommendation', 'HOLD')
            ai_rec = ai_analysis.get('ai_recommendation', 'HOLD')
            ai_confidence = ai_analysis.get('ai_confidence', 0.5)
            
            # Determine final recommendation
            final_recommendation = self._determine_final_recommendation(
                technical_rec, ai_rec, ai_confidence
            )
            
            # Enhanced analysis summary
            combined['final_recommendation'] = final_recommendation
            combined['analysis_summary'] = {
                'technical_recommendation': technical_rec,
                'ai_recommendation': ai_rec,
                'ai_confidence': ai_confidence,
                'final_recommendation': final_recommendation,
                'key_factors': ai_analysis.get('key_insights', []),
                'risk_assessment': ai_analysis.get('risk_factors', []),
                'target_price_range': ai_analysis.get('target_price_range', {}),
                'time_horizon': ai_analysis.get('time_horizon', 'MEDIUM')
            }
            
            return combined
            
        except Exception as e:
            self.logger.error(f"❌ Error combining technical and AI analysis: {e}")
            return technical_data
    
    def _determine_final_recommendation(self, technical_rec: str, ai_rec: str, ai_confidence: float) -> str:
        """Determine final recommendation based on technical and AI analysis"""
        try:
            if ai_confidence < 0.3:
                return technical_rec
            elif ai_confidence > 0.8 and ai_rec == technical_rec:
                if ai_rec == 'BUY':
                    return '적극매수'
                else:
                    return technical_rec
            elif ai_rec == technical_rec:
                return technical_rec
            else:
                if ai_confidence > 0.7:
                    return ai_rec
                else:
                    return '관망'
        except Exception as e:
            self.logger.error(f"❌ Error determining final recommendation: {e}")
            return technical_rec
    
    def _save_analysis_data(self, stock_code: str, data_type: str, data: any) -> None:
        """Save analysis data to data directory"""
        try:
            import os
            from pathlib import Path
            
            # Create data directory if it doesn't exist
            data_dir = Path('data')
            data_dir.mkdir(exist_ok=True)
            
            # Create timestamp for filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{stock_code}_{data_type}_{timestamp}.json"
            filepath = data_dir / filename
            
            # Save data as JSON
            if isinstance(data, str):
                # For text data like prompts
                save_data = {
                    'stock_code': stock_code,
                    'data_type': data_type,
                    'timestamp': timestamp,
                    'content': data
                }
            else:
                # For dict data like analysis results
                save_data = data
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 {stock_code} {data_type} 데이터 저장: {filepath}")
            
        except Exception as e:
            self.logger.error(f"❌ {stock_code} 데이터 저장 실패: {e}")
    
    def get_formatted_analysis_sentences(self, ai_analysis: Dict) -> List[str]:
        """Convert AI analysis reasoning into formatted sentences for Slack display"""
        try:
            reasoning = ai_analysis.get('ai_reasoning', '')
            if not reasoning:
                return ["AI 분석 정보가 없습니다."]
            
            # Split into sentences and clean up
            sentences = []
            
            # Split by common sentence endings
            raw_sentences = reasoning.replace('。', '.').split('.')
            
            for sentence in raw_sentences:
                cleaned = sentence.strip()
                if cleaned and len(cleaned) > 10:  # Filter out very short fragments
                    # Ensure sentence ends properly
                    if not cleaned.endswith(('.', '!', '?')):
                        cleaned += '.'
                    sentences.append(cleaned)
            
            # If no proper sentences found, return the original reasoning
            if not sentences:
                return [reasoning[:200] + "..." if len(reasoning) > 200 else reasoning]
            
            # Limit to 4 sentences for Slack display
            return sentences[:4]
            
        except Exception as e:
            self.logger.error(f"❌ AI 분석 문장 포맷팅 실패: {e}")
            return ["AI 분석 정보를 처리하는 중 오류가 발생했습니다."]
    
    def get_market_sentiment(self, market_indices: Dict = None) -> Dict[str, Any]:
        """Analyze overall market sentiment"""
        if not self.client:
            return {}
        
        try:
            self.logger.info("🤖 Analyzing market sentiment")
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            prompt = f"""
현재 시간: {current_time}

한국 증시 현재 상황:
{json.dumps(market_indices, ensure_ascii=False, indent=2) if market_indices else "데이터 없음"}

현재 한국 증시(KOSPI/KOSDAQ)의 전반적인 시장 심리와 향후 전망을 분석해 주세요.
다음 요소들을 고려해 주세요:
1. 국내외 경제 상황
2. 주요 이슈 및 정책
3. 글로벌 시장 동향
4. 섹터별 전망

JSON 형식으로 응답해 주세요.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a Korean stock market expert. Analyze market sentiment and provide insights in JSON format with fields:
                        sentiment_score (-1 to 1), market_outlook, key_factors, risks, opportunities, recommended_strategy."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            sentiment_analysis = json.loads(response.choices[0].message.content)
            sentiment_analysis['analysis_timestamp'] = datetime.now().isoformat()
            
            self.logger.info("✅ Market sentiment analysis completed")
            return sentiment_analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error in market sentiment analysis: {e}")
            return {}

