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
    
    def analyze_stocks(self, stock_data: Dict[str, Dict], market_data: Dict[str, Dict] = None) -> Dict[str, Dict]:
        """Analyze stocks and provide buy/sell recommendations"""
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

