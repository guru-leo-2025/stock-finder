"""
Technical Analysis Module for Stock Analysis
Based on readme.txt implementation with TA-Lib indicators
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("⚠️ Warning: TA-Lib not available, using alternative implementations")

class TechnicalAnalyzer:
    """Technical analysis for stock data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_stock(self, stock_code: str, price_data: pd.DataFrame, stock_name: str = None) -> Dict[str, Any]:
        """
        Analyze single stock with technical indicators and prepare for AI analysis
        
        Args:
            stock_code: Stock code (e.g., '005930')
            price_data: DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume']
            stock_name: Optional stock name for better AI context
            
        Returns:
            Dict containing technical analysis results ready for AI processing
        """
        try:
            if price_data.empty or len(price_data) < 20:
                self.logger.warning(f"❌ Insufficient data for {stock_code}")
                return self._get_empty_analysis()
                
            # Calculate technical indicators
            technical_indicators = self._calculate_technical_indicators(price_data)
            
            # Analyze buy signals
            buy_signals = self._analyze_buy_signals(technical_indicators, price_data)
            
            # Calculate detailed technical scores for each indicator
            detailed_scores = self._calculate_detailed_scores(technical_indicators, buy_signals)
            
            # Calculate overall technical score
            technical_score = detailed_scores['overall_score']
            
            # Calculate risk level
            risk_level = self._calculate_risk_level(technical_indicators)
            
            # Get current values
            current_values = self._get_current_values(technical_indicators, price_data)
            
            # Prepare technical summary for AI analysis
            technical_summary = self._prepare_ai_analysis_data(
                technical_indicators, buy_signals, detailed_scores, current_values, price_data
            )
            
            return {
                "stock_code": stock_code,
                "stock_name": stock_name or stock_code,
                "technical_score": technical_score,
                "detailed_scores": detailed_scores,
                "buy_signals": buy_signals,
                "risk_level": risk_level,
                "indicators": current_values,
                "recommendation": self._get_recommendation(technical_score, buy_signals, risk_level),
                "analysis_time": datetime.now().isoformat(),
                "technical_summary": technical_summary,  # New field for AI analysis
                "market_data": {
                    "current_price": float(price_data['close'].iloc[-1]) if not price_data.empty else 0.0,
                    "volume": int(price_data['volume'].iloc[-1]) if not price_data.empty else 0,
                    "high_52w": float(price_data['high'].max()) if not price_data.empty else 0.0,
                    "low_52w": float(price_data['low'].min()) if not price_data.empty else 0.0,
                    "avg_volume_20d": float(price_data['volume'].tail(20).mean()) if len(price_data) >= 20 else 0.0
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Technical analysis failed for {stock_code}: {e}")
            return self._get_empty_analysis()
    
    def _calculate_technical_indicators(self, price_data: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Calculate all technical indicators"""
        try:
            close = price_data['close'].values.astype(float)
            high = price_data['high'].values.astype(float)
            low = price_data['low'].values.astype(float)
            volume = price_data['volume'].values.astype(float)
            
            if TALIB_AVAILABLE:
                # Use TA-Lib if available
                return {
                    'sma_5': talib.SMA(close, timeperiod=5),
                    'sma_20': talib.SMA(close, timeperiod=20),
                    'sma_60': talib.SMA(close, timeperiod=60),
                    'rsi': talib.RSI(close, timeperiod=14),
                    'macd': talib.MACD(close)[0],
                    'macd_signal': talib.MACD(close)[1],
                    'macd_hist': talib.MACD(close)[2],
                    'bb_upper': talib.BBANDS(close)[0],
                    'bb_middle': talib.BBANDS(close)[1],
                    'bb_lower': talib.BBANDS(close)[2],
                    'stoch_k': talib.STOCH(high, low, close)[0],
                    'stoch_d': talib.STOCH(high, low, close)[1],
                    'close': close,
                    'volume': volume
                }
            else:
                # Use alternative implementations
                return self._calculate_indicators_alternative(close, high, low, volume)
                
        except Exception as e:
            self.logger.error(f"❌ Indicator calculation failed: {e}")
            return {}
    
    def _calculate_indicators_alternative(self, close: np.ndarray, high: np.ndarray, low: np.ndarray, volume: np.ndarray) -> Dict[str, np.ndarray]:
        """Alternative indicator calculations without TA-Lib"""
        try:
            indicators = {
                'close': close,
                'volume': volume
            }
            
            # Simple Moving Averages
            indicators['sma_5'] = self._sma(close, 5)
            indicators['sma_20'] = self._sma(close, 20)
            indicators['sma_60'] = self._sma(close, 60)
            
            # RSI
            indicators['rsi'] = self._rsi(close, 14)
            
            # MACD
            macd_data = self._macd(close)
            indicators['macd'] = macd_data['macd']
            indicators['macd_signal'] = macd_data['signal']
            indicators['macd_hist'] = macd_data['histogram']
            
            # Bollinger Bands
            bb_data = self._bollinger_bands(close, 20, 2)
            indicators['bb_upper'] = bb_data['upper']
            indicators['bb_middle'] = bb_data['middle']
            indicators['bb_lower'] = bb_data['lower']
            
            # Stochastic Oscillator
            stoch_data = self._stochastic(high, low, close, 14, 3)
            indicators['stoch_k'] = stoch_data['k']
            indicators['stoch_d'] = stoch_data['d']
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"❌ Alternative indicator calculation failed: {e}")
            return {}
    
    def _sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average"""
        result = np.full_like(data, np.nan)
        for i in range(period - 1, len(data)):
            result[i] = np.mean(data[i - period + 1:i + 1])
        return result
    
    def _rsi(self, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Relative Strength Index"""
        delta = np.diff(close)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        # Calculate average gain and loss
        avg_gain = np.full(len(close), np.nan)
        avg_loss = np.full(len(close), np.nan)
        
        # Initial averages
        if len(gain) >= period:
            avg_gain[period] = np.mean(gain[:period])
            avg_loss[period] = np.mean(loss[:period])
            
            # Smoothed averages
            for i in range(period + 1, len(close)):
                avg_gain[i] = (avg_gain[i-1] * (period - 1) + gain[i-1]) / period
                avg_loss[i] = (avg_loss[i-1] * (period - 1) + loss[i-1]) / period
        
        # Calculate RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _macd(self, close: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, np.ndarray]:
        """MACD Indicator"""
        ema_fast = self._ema(close, fast)
        ema_slow = self._ema(close, slow)
        macd = ema_fast - ema_slow
        signal_line = self._ema(macd, signal)
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average"""
        alpha = 2.0 / (period + 1.0)
        result = np.full_like(data, np.nan)
        
        # Start with first valid value
        first_valid = 0
        while first_valid < len(data) and np.isnan(data[first_valid]):
            first_valid += 1
            
        if first_valid < len(data):
            result[first_valid] = data[first_valid]
            
            for i in range(first_valid + 1, len(data)):
                if not np.isnan(data[i]):
                    result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
                else:
                    result[i] = result[i-1]
                    
        return result
    
    def _bollinger_bands(self, close: np.ndarray, period: int = 20, std_dev: float = 2) -> Dict[str, np.ndarray]:
        """Bollinger Bands"""
        sma = self._sma(close, period)
        
        # Calculate rolling standard deviation
        rolling_std = np.full_like(close, np.nan)
        for i in range(period - 1, len(close)):
            rolling_std[i] = np.std(close[i - period + 1:i + 1])
        
        upper = sma + (rolling_std * std_dev)
        lower = sma - (rolling_std * std_dev)
        
        return {
            'upper': upper,
            'middle': sma,
            'lower': lower
        }
    
    def _stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14, d_period: int = 3) -> Dict[str, np.ndarray]:
        """Stochastic Oscillator"""
        k_values = np.full_like(close, np.nan)
        
        for i in range(k_period - 1, len(close)):
            highest_high = np.max(high[i - k_period + 1:i + 1])
            lowest_low = np.min(low[i - k_period + 1:i + 1])
            
            if highest_high != lowest_low:
                k_values[i] = ((close[i] - lowest_low) / (highest_high - lowest_low)) * 100
            else:
                k_values[i] = 50  # Default to middle value
        
        # %D is SMA of %K
        d_values = self._sma(k_values, d_period)
        
        return {
            'k': k_values,
            'd': d_values
        }
    
    def _analyze_buy_signals(self, indicators: Dict[str, np.ndarray], price_data: pd.DataFrame) -> List[str]:
        """Analyze buy signals based on technical indicators"""
        buy_signals = []
        
        try:
            # Golden Cross (SMA5 > SMA20)
            if (len(indicators['sma_5']) > 1 and len(indicators['sma_20']) > 1 and
                indicators['sma_5'][-1] > indicators['sma_20'][-1] and
                indicators['sma_5'][-2] <= indicators['sma_20'][-2]):
                buy_signals.append("골든크로스")
            
            # RSI Oversold (RSI < 30)
            if len(indicators['rsi']) > 0 and indicators['rsi'][-1] < 30:
                buy_signals.append("RSI 과매도")
            
            # RSI Recovery (30 < RSI < 50 after oversold)
            if (len(indicators['rsi']) > 1 and 
                30 < indicators['rsi'][-1] < 50 and indicators['rsi'][-2] < 30):
                buy_signals.append("RSI 회복")
            
            # MACD Golden Cross
            if (len(indicators['macd']) > 1 and len(indicators['macd_signal']) > 1 and
                indicators['macd'][-1] > indicators['macd_signal'][-1] and
                indicators['macd'][-2] <= indicators['macd_signal'][-2]):
                buy_signals.append("MACD 상승전환")
            
            # Bollinger Band Lower Touch
            if (len(indicators['bb_lower']) > 0 and 
                indicators['close'][-1] <= indicators['bb_lower'][-1] * 1.02):
                buy_signals.append("볼린저밴드 하단 근접")
            
            # Volume Surge (거래량 급증)
            if len(indicators['volume']) > 5:
                avg_volume = np.mean(indicators['volume'][-5:])
                recent_volume = indicators['volume'][-1]
                if recent_volume > avg_volume * 1.5:
                    buy_signals.append("거래량 급증")
            
            # Stochastic Oversold
            if (len(indicators['stoch_k']) > 0 and len(indicators['stoch_d']) > 0 and
                indicators['stoch_k'][-1] < 20 and indicators['stoch_d'][-1] < 20):
                buy_signals.append("스토캐스틱 과매도")
                
        except Exception as e:
            self.logger.error(f"❌ Buy signal analysis failed: {e}")
            
        return buy_signals
    
    def _calculate_detailed_scores(self, indicators: Dict[str, np.ndarray], buy_signals: List[str]) -> Dict[str, Any]:
        """Calculate detailed scores for each technical indicator"""
        try:
            scores = {
                'base_score': 50.0,
                'buy_signals_score': 0.0,
                'trend_score': 0.0,
                'rsi_score': 0.0,
                'macd_score': 0.0,
                'volume_score': 0.0,
                'bollinger_score': 0.0,
                'stochastic_score': 0.0,
                'overall_score': 50.0
            }
            
            # Buy signals scoring (max +30 points)
            signals_score = len(buy_signals) * 10
            scores['buy_signals_score'] = min(30, signals_score)
            
            # Trend analysis scoring (max +15 points)
            if (len(indicators['sma_5']) > 0 and len(indicators['sma_20']) > 0 and
                indicators['sma_5'][-1] > indicators['sma_20'][-1]):
                scores['trend_score'] = 15  # Uptrend
                
                # Additional points for strong trend
                if (len(indicators['sma_60']) > 0 and 
                    indicators['sma_5'][-1] > indicators['sma_20'][-1] > indicators['sma_60'][-1]):
                    scores['trend_score'] = 20  # Strong uptrend
            elif (len(indicators['sma_5']) > 0 and len(indicators['sma_20']) > 0 and
                  indicators['sma_5'][-1] < indicators['sma_20'][-1]):
                scores['trend_score'] = -10  # Downtrend
            
            # RSI scoring (max +15 points, min -15 points)
            if len(indicators['rsi']) > 0:
                rsi = indicators['rsi'][-1]
                if 40 <= rsi <= 60:
                    scores['rsi_score'] = 15  # Healthy RSI
                elif 30 <= rsi < 40:
                    scores['rsi_score'] = 10   # Recovering from oversold
                elif 60 < rsi <= 70:
                    scores['rsi_score'] = 5    # Slightly overbought but acceptable
                elif rsi < 30:
                    scores['rsi_score'] = -5   # Oversold (could be opportunity)
                elif rsi > 70:
                    scores['rsi_score'] = -15  # Overbought warning
            
            # MACD scoring (max +10 points, min -10 points)
            if (len(indicators['macd']) > 0 and len(indicators['macd_signal']) > 0):
                macd = indicators['macd'][-1]
                signal = indicators['macd_signal'][-1]
                if macd > signal:
                    scores['macd_score'] = 10  # Bullish MACD
                else:
                    scores['macd_score'] = -5  # Bearish MACD
                
                # Additional scoring for MACD momentum
                if len(indicators['macd']) > 1:
                    macd_momentum = indicators['macd'][-1] - indicators['macd'][-2]
                    if macd_momentum > 0:
                        scores['macd_score'] += 2  # Positive momentum
            
            # Volume scoring (max +10 points)
            if len(indicators['volume']) > 10:
                recent_avg = np.mean(indicators['volume'][-5:])
                older_avg = np.mean(indicators['volume'][-10:-5])
                if recent_avg > older_avg * 1.2:
                    scores['volume_score'] = 10  # High volume
                elif recent_avg > older_avg:
                    scores['volume_score'] = 5   # Moderate volume increase
            
            # Bollinger Bands scoring (max +10 points, min -10 points)
            if (len(indicators['bb_upper']) > 0 and len(indicators['bb_lower']) > 0 and 
                len(indicators['close']) > 0):
                price = indicators['close'][-1]
                upper = indicators['bb_upper'][-1]
                lower = indicators['bb_lower'][-1]
                middle = indicators['bb_middle'][-1]
                
                bb_position = (price - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
                
                if 0.3 <= bb_position <= 0.7:
                    scores['bollinger_score'] = 10  # Good position
                elif bb_position < 0.2:
                    scores['bollinger_score'] = 5   # Near lower band (potential buy)
                elif bb_position > 0.8:
                    scores['bollinger_score'] = -10  # Near upper band (overbought)
            
            # Stochastic scoring (max +10 points, min -10 points)
            if (len(indicators['stoch_k']) > 0 and len(indicators['stoch_d']) > 0):
                k = indicators['stoch_k'][-1]
                d = indicators['stoch_d'][-1]
                
                if 20 <= k <= 80 and 20 <= d <= 80:
                    scores['stochastic_score'] = 10  # Healthy range
                elif k < 20 and d < 20:
                    scores['stochastic_score'] = 5   # Oversold (potential opportunity)
                elif k > 80 and d > 80:
                    scores['stochastic_score'] = -10  # Overbought
            
            # Calculate overall score
            overall = (scores['base_score'] + 
                      scores['buy_signals_score'] + 
                      scores['trend_score'] + 
                      scores['rsi_score'] + 
                      scores['macd_score'] + 
                      scores['volume_score'] + 
                      scores['bollinger_score'] + 
                      scores['stochastic_score'])
            
            scores['overall_score'] = min(100, max(0, overall))
            
            return scores
            
        except Exception as e:
            self.logger.error(f"❌ Detailed score calculation failed: {e}")
            return {
                'base_score': 50.0,
                'buy_signals_score': 0.0,
                'trend_score': 0.0,
                'rsi_score': 0.0,
                'macd_score': 0.0,
                'volume_score': 0.0,
                'bollinger_score': 0.0,
                'stochastic_score': 0.0,
                'overall_score': 50.0
            }
    
    def _calculate_technical_score(self, indicators: Dict[str, np.ndarray], buy_signals: List[str]) -> float:
        """Calculate technical analysis score (0-100)"""
        score = 50.0  # Base score
        
        try:
            # Buy signals boost
            score += len(buy_signals) * 10
            
            # Trend analysis
            if (len(indicators['sma_5']) > 0 and len(indicators['sma_20']) > 0 and
                indicators['sma_5'][-1] > indicators['sma_20'][-1]):
                score += 15  # Uptrend
            
            # RSI analysis
            if len(indicators['rsi']) > 0:
                rsi = indicators['rsi'][-1]
                if 40 <= rsi <= 60:
                    score += 10  # Healthy RSI
                elif 30 <= rsi < 40:
                    score += 5   # Recovering from oversold
                elif rsi > 70:
                    score -= 10  # Overbought warning
            
            # MACD momentum
            if (len(indicators['macd']) > 0 and len(indicators['macd_signal']) > 0 and
                indicators['macd'][-1] > indicators['macd_signal'][-1]):
                score += 8
            
            # Volume confirmation
            if len(indicators['volume']) > 10:
                recent_avg = np.mean(indicators['volume'][-5:])
                older_avg = np.mean(indicators['volume'][-10:-5])
                if recent_avg > older_avg:
                    score += 5
                    
        except Exception as e:
            self.logger.error(f"❌ Score calculation failed: {e}")
            
        return min(100, max(0, score))
    
    def _calculate_risk_level(self, indicators: Dict[str, np.ndarray]) -> str:
        """Calculate risk level based on technical indicators"""
        risk_score = 0
        
        try:
            # High RSI = Higher risk
            if len(indicators['rsi']) > 0 and indicators['rsi'][-1] > 70:
                risk_score += 30
            
            # Price near Bollinger Band upper = Higher risk
            if (len(indicators['bb_upper']) > 0 and len(indicators['close']) > 0 and
                indicators['close'][-1] >= indicators['bb_upper'][-1] * 0.98):
                risk_score += 25
            
            # Overbought Stochastic = Higher risk
            if (len(indicators['stoch_k']) > 0 and len(indicators['stoch_d']) > 0 and
                indicators['stoch_k'][-1] > 80 and indicators['stoch_d'][-1] > 80):
                risk_score += 20
                
            # High volatility check
            if len(indicators['close']) > 20:
                recent_std = np.std(indicators['close'][-20:])
                price_mean = np.mean(indicators['close'][-20:])
                volatility = (recent_std / price_mean) * 100
                if volatility > 5:  # 5% daily volatility
                    risk_score += 15
                    
        except Exception as e:
            self.logger.error(f"❌ Risk calculation failed: {e}")
            
        if risk_score < 30:
            return "낮음"
        elif risk_score < 60:
            return "보통"
        else:
            return "높음"
    
    def _get_current_values(self, indicators: Dict[str, np.ndarray], price_data: pd.DataFrame) -> Dict[str, float]:
        """Get current values of key indicators"""
        try:
            return {
                'rsi': float(indicators['rsi'][-1]) if len(indicators['rsi']) > 0 else 50.0,
                'macd': float(indicators['macd'][-1]) if len(indicators['macd']) > 0 else 0.0,
                'macd_signal': float(indicators['macd_signal'][-1]) if len(indicators['macd_signal']) > 0 else 0.0,
                'sma_5': float(indicators['sma_5'][-1]) if len(indicators['sma_5']) > 0 else 0.0,
                'sma_20': float(indicators['sma_20'][-1]) if len(indicators['sma_20']) > 0 else 0.0,
                'current_price': float(price_data['close'].iloc[-1]) if not price_data.empty else 0.0,
                'stoch_k': float(indicators['stoch_k'][-1]) if len(indicators['stoch_k']) > 0 else 50.0,
                'stoch_d': float(indicators['stoch_d'][-1]) if len(indicators['stoch_d']) > 0 else 50.0
            }
        except Exception as e:
            self.logger.error(f"❌ Getting current values failed: {e}")
            return {}
    
    def _get_recommendation(self, technical_score: float, buy_signals: List[str], risk_level: str) -> str:
        """Get buy/sell/hold recommendation"""
        if technical_score >= 75 and len(buy_signals) >= 2 and risk_level != "높음":
            return "적극매수"
        elif technical_score >= 65 and len(buy_signals) >= 1:
            return "매수"
        elif technical_score >= 55:
            return "보유"
        elif technical_score < 45:
            return "매도고려"
        else:
            return "관망"
    
    def _get_empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure for failed cases"""
        return {
            "stock_code": "",
            "technical_score": 50.0,
            "buy_signals": [],
            "risk_level": "보통",
            "indicators": {},
            "recommendation": "관망",
            "analysis_time": datetime.now().isoformat()
        }
    
    def analyze_multiple_stocks(self, stocks_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
        """Analyze multiple stocks"""
        results = {}
        
        for stock_code, price_data in stocks_data.items():
            try:
                analysis = self.analyze_stock(stock_code, price_data)
                results[stock_code] = analysis
                self.logger.info(f"✅ Technical analysis completed for {stock_code}")
            except Exception as e:
                self.logger.error(f"❌ Failed to analyze {stock_code}: {e}")
                results[stock_code] = self._get_empty_analysis()
                
        return results
    
    def _prepare_ai_analysis_data(self, indicators: Dict[str, np.ndarray], buy_signals: List[str], 
                                detailed_scores: Dict[str, Any], current_values: Dict[str, float], 
                                price_data: pd.DataFrame) -> Dict[str, Any]:
        """Prepare technical analysis data for AI processing"""
        try:
            # Price trend analysis
            price_trend = "상승" if len(indicators['close']) > 1 and indicators['close'][-1] > indicators['close'][-5] else "하락"
            
            # Volume trend analysis
            volume_trend = "증가" if len(indicators['volume']) > 5 and np.mean(indicators['volume'][-3:]) > np.mean(indicators['volume'][-10:-3]) else "감소"
            
            # Moving average position
            ma_position = "상승"
            if (len(indicators['sma_5']) > 0 and len(indicators['sma_20']) > 0 and len(indicators['sma_60']) > 0):
                if indicators['sma_5'][-1] > indicators['sma_20'][-1] > indicators['sma_60'][-1]:
                    ma_position = "강한상승"
                elif indicators['sma_5'][-1] < indicators['sma_20'][-1] < indicators['sma_60'][-1]:
                    ma_position = "강한하락"
                elif indicators['sma_5'][-1] > indicators['sma_20'][-1]:
                    ma_position = "상승"
                else:
                    ma_position = "하락"
            
            # Volatility analysis
            volatility = "보통"
            if len(indicators['close']) > 20:
                price_std = np.std(indicators['close'][-20:])
                price_mean = np.mean(indicators['close'][-20:])
                volatility_pct = (price_std / price_mean) * 100
                if volatility_pct > 5:
                    volatility = "높음"
                elif volatility_pct < 2:
                    volatility = "낮음"
            
            return {
                "price_trend": price_trend,
                "volume_trend": volume_trend,
                "moving_average_position": ma_position,
                "volatility": volatility,
                "rsi_status": "과매수" if current_values.get('rsi', 50) > 70 else "과매도" if current_values.get('rsi', 50) < 30 else "적정",
                "macd_status": "상승" if current_values.get('macd', 0) > current_values.get('macd_signal', 0) else "하락",
                "bollinger_position": self._get_bollinger_position(indicators, current_values),
                "support_resistance": self._get_support_resistance_levels(price_data),
                "momentum_analysis": self._analyze_momentum(indicators),
                "buy_signals_summary": f"{len(buy_signals)}개 매수신호: {', '.join(buy_signals[:3])}" if buy_signals else "매수신호 없음"
            }
            
        except Exception as e:
            self.logger.error(f"❌ AI analysis data preparation failed: {e}")
            return {
                "price_trend": "분석불가",
                "volume_trend": "분석불가",
                "moving_average_position": "분석불가",
                "volatility": "분석불가",
                "rsi_status": "분석불가",
                "macd_status": "분석불가",
                "bollinger_position": "분석불가",
                "support_resistance": {},
                "momentum_analysis": "분석불가",
                "buy_signals_summary": "분석불가"
            }
    
    def _get_bollinger_position(self, indicators: Dict[str, np.ndarray], current_values: Dict[str, float]) -> str:
        """Get Bollinger Band position description"""
        try:
            if len(indicators['bb_upper']) > 0 and len(indicators['bb_lower']) > 0:
                current_price = current_values.get('current_price', 0)
                upper = indicators['bb_upper'][-1]
                lower = indicators['bb_lower'][-1]
                middle = indicators['bb_middle'][-1]
                
                if current_price > upper:
                    return "상단밴드 돌파"
                elif current_price > middle:
                    return "중간선 위"
                elif current_price > lower:
                    return "중간선 아래"
                else:
                    return "하단밴드 근접"
            return "분석불가"
        except:
            return "분석불가"
    
    def _get_support_resistance_levels(self, price_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate key support and resistance levels"""
        try:
            if len(price_data) < 20:
                return {}
            
            recent_high = float(price_data['high'].tail(20).max())
            recent_low = float(price_data['low'].tail(20).min())
            current_price = float(price_data['close'].iloc[-1])
            
            return {
                "support_level": recent_low,
                "resistance_level": recent_high,
                "current_position": (current_price - recent_low) / (recent_high - recent_low) * 100 if recent_high != recent_low else 50
            }
        except:
            return {}
    
    def _analyze_momentum(self, indicators: Dict[str, np.ndarray]) -> str:
        """Analyze price momentum"""
        try:
            if len(indicators['close']) < 5:
                return "분석불가"
            
            # Recent price changes
            recent_change = (indicators['close'][-1] - indicators['close'][-5]) / indicators['close'][-5] * 100
            
            # MACD momentum
            macd_momentum = "상승" if len(indicators['macd_hist']) > 1 and indicators['macd_hist'][-1] > indicators['macd_hist'][-2] else "하락"
            
            if recent_change > 3:
                return f"강한상승모멘텀 (+{recent_change:.1f}%, MACD {macd_momentum})"
            elif recent_change > 0:
                return f"상승모멘텀 (+{recent_change:.1f}%, MACD {macd_momentum})"
            elif recent_change < -3:
                return f"강한하락모멘텀 ({recent_change:.1f}%, MACD {macd_momentum})"
            else:
                return f"약한하락모멘텀 ({recent_change:.1f}%, MACD {macd_momentum})"
        except:
            return "분석불가"
    
    def get_summary_analysis(self, all_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary analysis of all stocks"""
        try:
            if not all_results:
                return {"summary": "분석할 종목이 없습니다"}
            
            # Count recommendations
            recommendations = {}
            risk_levels = {"낮음": 0, "보통": 0, "높음": 0}
            total_signals = []
            scores = []
            
            for stock_code, analysis in all_results.items():
                rec = analysis.get('recommendation', '관망')
                recommendations[rec] = recommendations.get(rec, 0) + 1
                
                risk = analysis.get('risk_level', '보통')
                risk_levels[risk] += 1
                
                total_signals.extend(analysis.get('buy_signals', []))
                scores.append(analysis.get('technical_score', 50))
            
            # Most common signals
            signal_counts = {}
            for signal in total_signals:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
            top_signals = sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            avg_score = sum(scores) / len(scores) if scores else 50
            
            # Market sentiment
            strong_buy = recommendations.get('적극매수', 0)
            buy = recommendations.get('매수', 0)
            total_positive = strong_buy + buy
            
            if total_positive >= len(all_results) * 0.6:
                market_sentiment = "강세"
            elif total_positive >= len(all_results) * 0.3:
                market_sentiment = "중립"
            else:
                market_sentiment = "약세"
            
            return {
                "total_stocks": len(all_results),
                "average_score": round(avg_score, 1),
                "market_sentiment": market_sentiment,
                "recommendations": recommendations,
                "risk_distribution": risk_levels,
                "top_signals": top_signals,
                "summary": f"총 {len(all_results)}개 종목 분석 완료. 평균 기술적 점수 {avg_score:.1f}점, 시장 심리: {market_sentiment}"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Summary analysis failed: {e}")
            return {"summary": "종합 분석 중 오류 발생"}


