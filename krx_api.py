"""
KRX Market Data API integration for additional stock information
"""
import requests
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import json

from config import config

class KRXMarketDataAPI:
    """KRX Market Data API client for additional stock information"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = config.krx.base_url
        self.api_key = config.krx.api_key
        
        # Request headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Referer': 'http://data.krx.co.kr/'
        }
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def get_market_data(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """Get comprehensive market data for stocks"""
        market_data = {}
        
        try:
            self.logger.info(f"📊 Fetching KRX market data for {len(stock_codes)} stocks")
            
            # Get basic market data
            basic_data = self._get_basic_market_data(stock_codes)
            market_data.update(basic_data)
            
            # Get financial indicators
            financial_data = self._get_financial_indicators(stock_codes)
            self._merge_data(market_data, financial_data)
            
            # Get trading data
            trading_data = self._get_trading_data(stock_codes)
            self._merge_data(market_data, trading_data)
            
            # Get sector information
            sector_data = self._get_sector_info(stock_codes)
            self._merge_data(market_data, sector_data)
            
            self.logger.info(f"✅ Successfully fetched KRX data for {len(market_data)} stocks")
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching KRX market data: {e}")
        
        return market_data
    
    def _get_basic_market_data(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """Get basic market data from KRX"""
        try:
            # KRX basic market data endpoint
            url = f"{self.base_url}/comm/bldAttendant/getJsonData.cmd"
            
            params = {
                'bld': 'dbms/MDC/STAT/standard/MDCSTAT01501',
                'mktId': 'ALL',  # All markets (KOSPI + KOSDAQ)
                'trdDd': datetime.now().strftime('%Y%m%d'),
                'money': '1',
                'csvxls_isNo': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            market_data = {}
            
            if 'OutBlock_1' in data:
                for item in data['OutBlock_1']:
                    stock_code = item.get('ISU_SRT_CD', '').strip()
                    if stock_code in stock_codes:
                        market_data[stock_code] = {
                            'market_cap': self._safe_int(item.get('MKTCAP', '0')),
                            'shares_outstanding': self._safe_int(item.get('LIST_SHRS', '0')),
                            'per': self._safe_float(item.get('PER', '0')),
                            'pbr': self._safe_float(item.get('PBR', '0')),
                            'dividend_yield': self._safe_float(item.get('DVD_YLD', '0')),
                        }
            
            self.logger.info(f"📈 Basic market data retrieved for {len(market_data)} stocks")
            return market_data
            
        except Exception as e:
            self.logger.error(f"❌ Error getting basic market data: {e}")
            return {}
    
    def _get_financial_indicators(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """Get financial indicators from KRX"""
        try:
            url = f"{self.base_url}/comm/bldAttendant/getJsonData.cmd"
            
            params = {
                'bld': 'dbms/MDC/STAT/standard/MDCSTAT03501',
                'mktId': 'ALL',
                'trdDd': datetime.now().strftime('%Y%m%d'),
                'csvxls_isNo': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            financial_data = {}
            
            if 'OutBlock_1' in data:
                for item in data['OutBlock_1']:
                    stock_code = item.get('ISU_SRT_CD', '').strip()
                    if stock_code in stock_codes:
                        financial_data[stock_code] = {
                            'roe': self._safe_float(item.get('ROE', '0')),
                            'roa': self._safe_float(item.get('ROA', '0')),
                            'debt_ratio': self._safe_float(item.get('DT_RT', '0')),
                            'current_ratio': self._safe_float(item.get('CUR_RT', '0')),
                        }
            
            self.logger.info(f"💰 Financial indicators retrieved for {len(financial_data)} stocks")
            return financial_data
            
        except Exception as e:
            self.logger.error(f"❌ Error getting financial indicators: {e}")
            return {}
    
    def _get_trading_data(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """Get trading data from KRX"""
        try:
            url = f"{self.base_url}/comm/bldAttendant/getJsonData.cmd"
            
            # Get recent 5 days of trading data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            params = {
                'bld': 'dbms/MDC/STAT/standard/MDCSTAT01701',
                'mktId': 'ALL',
                'strtDd': start_date.strftime('%Y%m%d'),
                'endDd': end_date.strftime('%Y%m%d'),
                'csvxls_isNo': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            trading_data = {}
            
            if 'OutBlock_1' in data:
                # Process trading data by stock code
                stock_trading = {}
                for item in data['OutBlock_1']:
                    stock_code = item.get('ISU_SRT_CD', '').strip()
                    if stock_code in stock_codes:
                        if stock_code not in stock_trading:
                            stock_trading[stock_code] = []
                        
                        stock_trading[stock_code].append({
                            'date': item.get('TRD_DD', ''),
                            'volume': self._safe_int(item.get('ACC_TRDVOL', '0')),
                            'amount': self._safe_int(item.get('ACC_TRDVAL', '0')),
                            'close_price': self._safe_int(item.get('TDD_CLSPRC', '0'))
                        })
                
                # Calculate trading metrics
                for stock_code, trades in stock_trading.items():
                    if trades:
                        recent_volumes = [t['volume'] for t in trades[-5:]]
                        avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
                        
                        trading_data[stock_code] = {
                            'avg_volume_5d': avg_volume,
                            'volume_trend': 'increasing' if len(recent_volumes) >= 2 and recent_volumes[-1] > recent_volumes[-2] else 'decreasing',
                            'trading_days': len(trades)
                        }
            
            self.logger.info(f"📊 Trading data retrieved for {len(trading_data)} stocks")
            return trading_data
            
        except Exception as e:
            self.logger.error(f"❌ Error getting trading data: {e}")
            return {}
    
    def _get_sector_info(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """Get sector information from KRX"""
        try:
            url = f"{self.base_url}/comm/bldAttendant/getJsonData.cmd"
            
            params = {
                'bld': 'dbms/MDC/STAT/standard/MDCSTAT03901',
                'mktId': 'ALL',
                'csvxls_isNo': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            sector_data = {}
            
            if 'OutBlock_1' in data:
                for item in data['OutBlock_1']:
                    stock_code = item.get('ISU_SRT_CD', '').strip()
                    if stock_code in stock_codes:
                        sector_data[stock_code] = {
                            'sector': item.get('IDX_IND_NM', 'Unknown'),
                            'industry': item.get('IDX_IND_NM', 'Unknown'),
                            'market': item.get('MKT_NM', 'Unknown')
                        }
            
            self.logger.info(f"🏭 Sector info retrieved for {len(sector_data)} stocks")
            return sector_data
            
        except Exception as e:
            self.logger.error(f"❌ Error getting sector info: {e}")
            return {}
    
    def get_market_indices(self) -> Dict[str, Any]:
        """Get major market indices (KOSPI, KOSDAQ)"""
        try:
            url = f"{self.base_url}/comm/bldAttendant/getJsonData.cmd"
            
            params = {
                'bld': 'dbms/MDC/STAT/standard/MDCSTAT00101',
                'trdDd': datetime.now().strftime('%Y%m%d'),
                'csvxls_isNo': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            indices = {}
            
            if 'OutBlock_1' in data:
                for item in data['OutBlock_1']:
                    index_name = item.get('IDX_NM', '')
                    if 'KOSPI' in index_name or 'KOSDAQ' in index_name:
                        indices[index_name] = {
                            'value': self._safe_float(item.get('CLSPRC_IDX', '0')),
                            'change': self._safe_float(item.get('FLUC_RT', '0')),
                            'volume': self._safe_int(item.get('ACC_TRDVOL', '0'))
                        }
            
            self.logger.info(f"📈 Retrieved {len(indices)} market indices")
            return indices
            
        except Exception as e:
            self.logger.error(f"❌ Error getting market indices: {e}")
            return {}
    
    def get_news_sentiment(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """Get news and sentiment data (placeholder - would need actual news API)"""
        # This is a placeholder for news sentiment analysis
        # In practice, you would integrate with news APIs like:
        # - Naver News API
        # - Financial news providers
        # - Social media sentiment analysis
        
        news_data = {}
        for stock_code in stock_codes:
            news_data[stock_code] = {
                'news_count_24h': 0,
                'sentiment_score': 0.0,  # -1 to 1 scale
                'recent_news': []
            }
        
        self.logger.info("📰 News sentiment data (placeholder)")
        return news_data
    
    def _merge_data(self, target: Dict, source: Dict):
        """Merge source data into target data"""
        for key, value in source.items():
            if key in target:
                target[key].update(value)
            else:
                target[key] = value
    
    def _safe_int(self, value: str) -> int:
        """Safely convert string to integer"""
        try:
            return int(str(value).replace(',', '').replace('-', '0'))
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value: str) -> float:
        """Safely convert string to float"""
        try:
            return float(str(value).replace(',', '').replace('-', '0'))
        except (ValueError, TypeError):
            return 0.0
    
    def close(self):
        """Close the session"""
        if hasattr(self, 'session'):
            self.session.close()

class MockKRXAPI:
    """Mock KRX API for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("🧪 Using Mock KRX API (Test Mode)")
    
    def get_market_data(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """Return mock market data"""
        market_data = {}
        
        for i, stock_code in enumerate(stock_codes):
            market_data[stock_code] = {
                'market_cap': 50000000 + (i * 10000000),  # Market cap in millions
                'shares_outstanding': 100000000 + (i * 5000000),
                'per': 15.5 + (i * 2.5),
                'pbr': 1.2 + (i * 0.3),
                'dividend_yield': 2.5 + (i * 0.5),
                'roe': 12.0 + (i * 2.0),
                'roa': 8.0 + (i * 1.5),
                'debt_ratio': 30.0 + (i * 5.0),
                'current_ratio': 150.0 + (i * 10.0),
                'avg_volume_5d': 1000000 + (i * 100000),
                'volume_trend': 'increasing' if i % 2 == 0 else 'decreasing',
                'trading_days': 5,
                'sector': ['Technology', 'Finance', 'Manufacturing', 'Retail', 'Energy'][i % 5],
                'industry': ['Semiconductors', 'Banking', 'Steel', 'Retail', 'Oil'][i % 5],
                'market': 'KOSPI' if i % 2 == 0 else 'KOSDAQ'
            }
        
        self.logger.info(f"🧪 Mock KRX data for {len(market_data)} stocks")
        return market_data
    
    def get_market_indices(self) -> Dict[str, Any]:
        """Return mock market indices"""
        return {
            'KOSPI': {'value': 2500.0, 'change': 1.5, 'volume': 500000000},
            'KOSDAQ': {'value': 800.0, 'change': -0.8, 'volume': 200000000}
        }
    
    def get_news_sentiment(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """Return mock news sentiment"""
        news_data = {}
        for i, stock_code in enumerate(stock_codes):
            news_data[stock_code] = {
                'news_count_24h': 5 + (i * 2),
                'sentiment_score': 0.1 + (i * 0.1) if i % 2 == 0 else -0.1 - (i * 0.1),
                'recent_news': [f"Mock news {j+1} for {stock_code}" for j in range(3)]
            }
        return news_data
    
    def close(self):
        pass