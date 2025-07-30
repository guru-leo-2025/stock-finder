"""
AI 분석 시스템 테스트 스크립트
"""

import logging
import json
from datetime import datetime
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ai_analysis():
    """AI 분석 시스템 테스트"""
    try:
        from ai_analyzer import AIStockAnalyzer
        from technical_analyzer import TechnicalAnalyzer
        
        logger.info("🧪 AI 분석 시스템 테스트 시작")
        
        # AI 분석기 초기화 테스트
        try:
            ai_analyzer = AIStockAnalyzer()
            logger.info("✅ AI 분석기 초기화 성공")
        except Exception as e:
            logger.error(f"❌ AI 분석기 초기화 실패: {e}")
            return False
        
        # 샘플 기술적 분석 데이터 생성
        sample_technical_data = {
            '005930': {  # 삼성전자
                'stock_code': '005930',
                'stock_name': '삼성전자',
                'technical_score': 72.5,
                'recommendation': '매수',
                'risk_level': '보통',
                'buy_signals': ['골든크로스', 'RSI 회복', '거래량 급증'],
                'indicators': {
                    'rsi': 58.2,
                    'macd': 0.0523,
                    'macd_signal': 0.0445,
                    'sma_5': 73500,
                    'sma_20': 71200,
                    'current_price': 74000,
                    'stoch_k': 65.4,
                    'stoch_d': 62.1
                },
                'market_data': {
                    'current_price': 74000,
                    'volume': 15420000,
                    'high_52w': 89000,
                    'low_52w': 58000
                },
                'technical_summary': {
                    'price_trend': '상승',
                    'volume_trend': '증가',
                    'moving_average_position': '강한상승',
                    'volatility': '보통',
                    'bollinger_position': '중간선 위',
                    'momentum_analysis': '상승모멘텀 (+2.3%, MACD 상승)'
                }
            }
        }
        
        # AI 분석 테스트
        logger.info("🤖 AI 분석 테스트 시작...")
        ai_results = ai_analyzer.analyze_stocks_with_technical_data(sample_technical_data)
        
        if ai_results:
            logger.info(f"✅ AI 분석 성공: {len(ai_results)}개 종목")
            
            # 결과 출력
            for stock_code, analysis in ai_results.items():
                logger.info(f"\n📊 {stock_code} 분석 결과:")
                logger.info(f"   종목명: {analysis.get('stock_name', 'N/A')}")
                logger.info(f"   기술적 점수: {analysis.get('technical_score', 'N/A')}")
                logger.info(f"   최종 추천: {analysis.get('final_recommendation', 'N/A')}")
                
                ai_analysis = analysis.get('ai_analysis', {})
                if ai_analysis:
                    logger.info(f"   AI 추천: {ai_analysis.get('ai_recommendation', 'N/A')}")
                    logger.info(f"   AI 신뢰도: {ai_analysis.get('ai_confidence', 'N/A')}")
                    logger.info(f"   AI 분석: {ai_analysis.get('ai_reasoning', 'N/A')[:100]}...")
                
                # 문장 포맷팅 테스트
                if ai_analysis and ai_analysis.get('ai_reasoning'):
                    sentences = ai_analyzer.get_formatted_analysis_sentences(ai_analysis)
                    logger.info(f"   포맷된 문장들:")
                    for i, sentence in enumerate(sentences, 1):
                        logger.info(f"     {i}. {sentence}")
            
            return True
        else:
            logger.error("❌ AI 분석 결과가 없습니다")
            return False
            
    except Exception as e:
        logger.error(f"❌ AI 분석 테스트 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def check_data_directory():
    """데이터 디렉토리 확인"""
    data_dir = Path('data')
    if data_dir.exists():
        files = list(data_dir.glob('*.json'))
        logger.info(f"📁 데이터 디렉토리: {len(files)}개 파일 발견")
        
        # 최근 파일 5개 표시
        recent_files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        for file in recent_files:
            logger.info(f"   📄 {file.name}")
    else:
        logger.info("📁 데이터 디렉토리가 아직 생성되지 않았습니다")

if __name__ == "__main__":
    logger.info("🚀 AI 분석 시스템 테스트 시작")
    
    # 데이터 디렉토리 확인
    check_data_directory()
    
    # AI 분석 테스트
    success = test_ai_analysis()
    
    if success:
        logger.info("✅ AI 분석 시스템 테스트 완료")
        
        # 데이터 디렉토리 재확인
        logger.info("\n📁 테스트 후 데이터 디렉토리 상태:")
        check_data_directory()
    else:
        logger.error("❌ AI 분석 시스템 테스트 실패")