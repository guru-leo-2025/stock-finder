"""
통합 분석 시스템 예시
Technical Analyzer -> AI Analyzer -> Slack Notifier 연동 데모

AI 모델: gpt-4o-mini-2024-07-18 (기본값)
환경변수 OPENAI_MODEL로 변경 가능
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from technical_analyzer import TechnicalAnalyzer
from ai_analyzer import AIStockAnalyzer
from slack_notifier import SlackNotifier

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_price_data(stock_code: str) -> pd.DataFrame:
    """샘플 주가 데이터 생성 (실제 사용시에는 키움 API에서 가져옴)"""
    dates = pd.date_range(start='2024-01-01', end='2025-01-30', freq='D')
    np.random.seed(hash(stock_code) % 1000)  # 종목별로 다른 시드
    
    # 기본 가격 설정
    base_price = np.random.randint(10000, 100000)
    prices = []
    volumes = []
    
    current_price = base_price
    for i in range(len(dates)):
        # 가격 변동 (랜덤워크 + 트렌드)
        change_pct = np.random.normal(0, 0.02)  # 평균 0%, 표준편차 2%
        if i < len(dates) * 0.3:  # 초기 30%는 하락 트렌드
            change_pct -= 0.005
        elif i > len(dates) * 0.7:  # 후반 30%는 상승 트렌드
            change_pct += 0.008
            
        current_price = current_price * (1 + change_pct)
        current_price = max(current_price, base_price * 0.5)  # 최소 50% 수준
        
        # OHLC 생성
        open_price = current_price * np.random.uniform(0.99, 1.01)
        high_price = max(open_price, current_price) * np.random.uniform(1.0, 1.03)
        low_price = min(open_price, current_price) * np.random.uniform(0.97, 1.0)
        close_price = current_price
        
        # 거래량 생성
        base_volume = np.random.randint(100000, 1000000)
        volume_multiplier = np.random.uniform(0.5, 2.0)
        if abs(change_pct) > 0.03:  # 큰 변동시 거래량 증가
            volume_multiplier *= 1.5
        volume = int(base_volume * volume_multiplier)
        
        prices.append({
            'date': dates[i],
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    return pd.DataFrame(prices)

def demonstrate_integrated_analysis():
    """통합 분석 시스템 데모"""
    logger.info("🚀 통합 분석 시스템 데모 시작")
    
    # 샘플 종목 리스트
    sample_stocks = {
        '005930': '삼성전자',
        '000660': 'SK하이닉스',
        '035420': 'NAVER',
        '005380': '현대차',
        '035720': '카카오'
    }
    
    try:
        # 1. 기술적 분석 수행
        logger.info("📈 1단계: 기술적 분석 수행")
        technical_analyzer = TechnicalAnalyzer()
        technical_results = {}
        
        for stock_code, stock_name in sample_stocks.items():
            # 샘플 주가 데이터 생성 (실제로는 키움 API에서 가져옴)
            price_data = create_sample_price_data(stock_code)
            
            # 기술적 분석 수행
            analysis = technical_analyzer.analyze_stock(stock_code, price_data, stock_name)
            technical_results[stock_code] = analysis
            
            logger.info(f"✅ {stock_name}({stock_code}) 기술적 분석 완료 - 점수: {analysis.get('technical_score', 0):.1f}점")
        
        # 2. AI 분석 수행
        logger.info("🤖 2단계: AI 분석 수행")
        ai_analyzer = AIStockAnalyzer()
        
        # 기술적 분석 결과를 AI로 강화
        ai_enhanced_results = ai_analyzer.analyze_stocks_with_technical_data(technical_results)
        
        logger.info(f"✅ AI 분석 완료 - {len(ai_enhanced_results)}개 종목 분석")
        
        # 3. Slack 알림 전송
        logger.info("📱 3단계: Slack 알림 전송")
        slack_notifier = SlackNotifier()
        
        # AI 강화 분석 결과를 Slack으로 전송
        success = slack_notifier.send_ai_enhanced_analysis(
            ai_enhanced_results, 
            "통합 분석 시스템 데모"
        )
        
        if success:
            logger.info("✅ Slack 알림 전송 완료")
        else:
            logger.error("❌ Slack 알림 전송 실패")
        
        # 4. 결과 요약 출력
        logger.info("📊 4단계: 결과 요약")
        print_analysis_summary(ai_enhanced_results)
        
    except Exception as e:
        logger.error(f"❌ 통합 분석 시스템 오류: {e}")
        import traceback
        traceback.print_exc()

def print_analysis_summary(results: dict):
    """분석 결과 요약 출력"""
    print("\n" + "="*80)
    print("📊 AI 강화 기술적 분석 결과 요약")
    print("="*80)
    
    for stock_code, analysis in results.items():
        stock_name = analysis.get('stock_name', stock_code)
        technical_score = analysis.get('technical_score', 0)
        final_rec = analysis.get('final_recommendation', analysis.get('recommendation', 'HOLD'))
        
        ai_analysis = analysis.get('ai_analysis', {})
        ai_confidence = ai_analysis.get('ai_confidence', 0)
        ai_rec = ai_analysis.get('ai_recommendation', 'HOLD')
        
        print(f"\n🏢 {stock_name} ({stock_code})")
        print(f"   📊 기술적 점수: {technical_score:.1f}점")
        print(f"   🤖 AI 추천: {ai_rec} (신뢰도: {ai_confidence:.1f})")
        print(f"   🎯 최종 추천: {final_rec}")
        
        # 주요 매수 신호
        buy_signals = analysis.get('buy_signals', [])
        if buy_signals:
            print(f"   📈 매수신호: {', '.join(buy_signals[:3])}")
        
        # AI 분석 요약
        ai_reasoning = ai_analysis.get('ai_reasoning', '')
        if ai_reasoning:
            summary = ai_reasoning[:100] + "..." if len(ai_reasoning) > 100 else ai_reasoning
            print(f"   💡 AI 분석: {summary}")
    
    print("\n" + "="*80)
    print("✅ 통합 분석 완료")
    print("="*80)

if __name__ == "__main__":
    demonstrate_integrated_analysis()