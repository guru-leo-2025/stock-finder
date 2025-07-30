"""
Kiwoom API integration for stock screening and data retrieval
"""
import sys
import time
import logging
import platform
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd

# PyQt5 imports for 32-bit Windows environment
try:
    if platform.architecture()[0] == '32bit':
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QAxContainer import QAxWidget
        from PyQt5.QtCore import QEventLoop, QTimer, pyqtSignal, QObject
        PYQT5_AVAILABLE = True
    else:
        PYQT5_AVAILABLE = False
        print("⚠️ Warning: 32-bit Python required for Kiwoom API")
except ImportError:
    PYQT5_AVAILABLE = False
    print("⚠️ Warning: PyQt5 not available")

from config import config

class KiwoomAPI(QObject):
    """Kiwoom OpenAPI+ integration for stock screening and trading"""
    
    # PyQt signals for event handling
    login_event = pyqtSignal()
    data_received = pyqtSignal()
    condition_event = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Check environment compatibility
        if not self._check_environment():
            self.ocx = None
            self.app = None
            return
        
        # Initialize Qt Application
        if QApplication.instance() is None:
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        
        # Initialize Kiwoom OCX
        try:
            self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
            self.logger.info("✅ Kiwoom OCX control created successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to create Kiwoom OCX control: {e}")
            self.ocx = None
            return
        
        # Connection state
        self.connected = False
        self.login_loop = None
        self.data_loop = None
        
        # Data storage
        self.screen_num = "1000"
        self.condition_data = {}
        self.condition_list = {}  # Store condition name -> index mapping
        self.condition_loaded = False  # 조건식 로드 완료 플래그
        
        # Connect signals
        self._connect_signals()
        
    def _check_environment(self) -> bool:
        """Check if environment supports Kiwoom API"""
        if platform.system() != 'Windows':
            self.logger.error("❌ Kiwoom API requires Windows OS")
            return False
        
        if platform.architecture()[0] != '32bit':
            self.logger.error("❌ Kiwoom API requires 32-bit Python")
            return False
        
        if not PYQT5_AVAILABLE:
            self.logger.error("❌ PyQt5 is required for Kiwoom API")
            return False
        
        return True
    
    def _connect_signals(self):
        """Connect Kiwoom OCX event signals"""
        if not self.ocx:
            return
        
        try:
            # Basic connection and data events
            self.ocx.OnEventConnect.connect(self._on_event_connect)
            self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
            self.ocx.OnReceiveRealData.connect(self._on_receive_real_data)
            
            # Condition events for screening
            self.ocx.OnReceiveConditionVer.connect(self._on_receive_condition_ver)
            self.ocx.OnReceiveTrCondition.connect(self._on_receive_tr_condition)
            self.ocx.OnReceiveRealCondition.connect(self._on_receive_real_condition)
            
            self.logger.info("✅ Kiwoom OCX signals connected")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect OCX signals: {e}")
    
    def connect(self) -> bool:
        """Connect to Kiwoom server with auto-login"""
        if not self.ocx:
            self.logger.error("❌ OCX not initialized")
            return False
        
        try:
            self.logger.info("🔄 Connecting to Kiwoom server...")
            
            # 자동 로그인 설정 (로그인 창이 뜨면 자동으로 정보 입력)
            if config.kiwoom.user_id and config.kiwoom.password:
                self.logger.info("🔑 Auto-login credentials configured")
                # 키움 자동 로그인 시도
                ret = self._perform_auto_login()
                if ret:
                    self.logger.info("✅ Auto-login successful")
                else:
                    self.logger.warning("⚠️ Auto-login failed, trying manual login...")
            
            # 일반 연결 시도
            self.login_loop = QEventLoop()
            self.ocx.CommConnect()
            self.login_loop.exec_()
            
            if self.connected:
                self.logger.info("✅ Connected to Kiwoom server")
                user_id = self.ocx.GetLoginInfo("USER_ID")
                user_name = self.ocx.GetLoginInfo("USER_NAME")
                self.logger.info(f"👤 User: {user_name} ({user_id})")
                return True
            else:
                self.logger.error("❌ Failed to connect to Kiwoom server")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Connection error: {e}")
            return False
    
    def _perform_auto_login(self) -> bool:
        """키움 자동 로그인 수행"""
        try:
            import win32gui
            import win32con
            import time
            
            # 로그인 창이 나타날 때까지 대기
            time.sleep(2)
            
            # 키움 로그인 창 찾기
            hwnd = win32gui.FindWindow(None, "Open API Login")
            if not hwnd:
                # 다른 가능한 창 제목들
                possible_titles = ["KHOpenAPI Login", "키움 OpenAPI", "로그인"]
                for title in possible_titles:
                    hwnd = win32gui.FindWindow(None, title)
                    if hwnd:
                        break
            
            if hwnd:
                self.logger.info(f"🔍 로그인 창 발견: {hwnd}")
                
                # 창을 활성화
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.5)
                
                # 자동 입력 (키보드 시뮬레이션)
                import win32api
                import win32clipboard
                
                # 사용자 ID 입력
                self._send_text_to_window(config.kiwoom.user_id)
                win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)  # Tab
                win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.2)
                
                # 비밀번호 입력
                self._send_text_to_window(config.kiwoom.password)
                win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)  # Tab
                win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.2)
                
                # 공인인증서 비밀번호 입력 (있는 경우)
                if config.kiwoom.cert_password:
                    self._send_text_to_window(config.kiwoom.cert_password)
                
                # Enter 키 입력 (로그인 실행)
                win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                
                self.logger.info("🔑 자동 로그인 정보 입력 완료")
                return True
                
            else:
                self.logger.warning("⚠️ 로그인 창을 찾을 수 없습니다")
                return False
                
        except ImportError:
            self.logger.warning("⚠️ win32gui 모듈을 찾을 수 없습니다. 수동 로그인 필요")
            return False
        except Exception as e:
            self.logger.error(f"❌ 자동 로그인 중 오류: {e}")
            return False
    
    def _send_text_to_window(self, text: str):
        """텍스트를 활성 창에 전송"""
        try:
            import win32clipboard
            import win32con
            import win32api
            
            # 클립보드 사용해서 텍스트 입력
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text)
            win32clipboard.CloseClipboard()
            
            # Ctrl+V로 붙여넣기
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('V'), 0, 0, 0)
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            
        except Exception as e:
            self.logger.debug(f"텍스트 입력 오류: {e}")
    
    def disconnect(self):
        """Disconnect from Kiwoom server"""
        if self.ocx and self.connected:
            self.ocx.CommTerminate()
            self.connected = False
            self.logger.info("🔌 Disconnected from Kiwoom server")
    
    def load_condition_list(self) -> bool:
        """Load screening condition list - 조건식 목록 로드"""
        if not self.connected:
            self.logger.error("❌ Not connected to Kiwoom server")
            return False
        
        try:
            self.logger.info("📋 조건식 목록 로드 요청...")
            
            # 조건식 로드 완료 플래그 초기화
            self.condition_loaded = False
            
            # 조건식 로드 요청 - OnReceiveConditionVer 이벤트 발생
            ret = self.ocx.GetConditionLoad()
            
            if ret == 1:
                self.logger.info("✅ 조건식 로드 요청 성공 - 이벤트 대기 중...")
                
                # 조건식 로드 완료까지 대기 (최대 10초)
                timeout = 0
                while not self.condition_loaded and timeout < 20:  # 20초로 증가
                    if hasattr(self, 'app') and self.app:
                        self.app.processEvents()  # Qt 이벤트 처리
                    time.sleep(0.5)
                    timeout += 0.5
                
                if not self.condition_loaded:
                    self.logger.error("❌ 조건식 로드 타임아웃 (20초)")
                    return False
                
                # 조건식 목록 가져오기
                condition_name_list = self.ocx.GetConditionNameList()
                
                if not condition_name_list:
                    self.logger.warning("⚠️ 조건식 목록이 비어있습니다")
                    self.logger.info("💡 키움 HTS에서 조건식을 생성하고 저장했는지 확인하세요")
                    return False
                
                self.logger.info(f"📋 조건식 원본 데이터: {condition_name_list}")
                
                # 조건식 파싱
                conditions = condition_name_list.split(';')[:-1]  # 마지막 빈 요소 제거
                
                if not conditions:
                    self.logger.warning("⚠️ 파싱된 조건식이 없습니다")
                    return False
                
                self.logger.info(f"✅ 총 {len(conditions)}개의 조건식 발견")
                self.logger.info("=" * 60)
                
                # 조건식 정보 저장 및 출력
                self.condition_list = {}
                for i, condition in enumerate(conditions, 1):
                    try:
                        parts = condition.split('^')
                        if len(parts) >= 2:
                            index = int(parts[0])
                            name = parts[1].strip()  # 공백 제거
                            self.condition_list[name] = index
                            self.logger.info(f"  {i:2d}. 조건명: '{name}' (인덱스: {index})")
                        else:
                            self.logger.warning(f"⚠️ 조건식 파싱 오류: {condition}")
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"⚠️ 조건식 파싱 실패: {condition} - {e}")
                
                self.logger.info("=" * 60)
                
                # 목표 조건식 확인
                target_condition = config.kiwoom.screening_condition
                if target_condition in self.condition_list:
                    self.logger.info(f"🎯 목표 조건식 '{target_condition}' 발견! (인덱스: {self.condition_list[target_condition]})")
                else:
                    self.logger.warning(f"⚠️ 목표 조건식 '{target_condition}'을 찾을 수 없습니다")
                    self.logger.info(f"📋 사용 가능한 조건식: {list(self.condition_list.keys())}")
                
                return len(self.condition_list) > 0
                
            else:
                self.logger.error("❌ 조건식 로드 요청 실패")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 조건식 로드 중 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def get_condition_stocks(self, condition_name: str = None, max_retries: int = 3) -> List[str]:
        """Get stocks from screening condition - 조건식으로 종목 검색 (재시도 로직 포함)"""
        if not condition_name:
            condition_name = config.kiwoom.screening_condition
        
        if not self.connected:
            self.logger.error("❌ 키움 서버에 연결되지 않음")
            return []
        
        # 재시도 로직
        for attempt in range(max_retries):
            try:
                self.logger.info(f"🔄 조건식 검색 시도 {attempt + 1}/{max_retries}")
                
                # 조건식 목록이 로드되었는지 확인
                if not hasattr(self, 'condition_list') or not self.condition_list:
                    self.logger.warning("⚠️ 조건식 목록이 로드되지 않음. 다시 로드 시도...")
                    if not self.load_condition_list():
                        self.logger.error("❌ 조건식 목록 로드 실패")
                        if attempt < max_retries - 1:
                            time.sleep(2)  # 2초 대기 후 재시도
                            continue
                        return []
                
                # 조건식 존재 여부 확인
                if condition_name not in self.condition_list:
                    self.logger.error(f"❌ 조건식 '{condition_name}'을 찾을 수 없습니다")
                    available = list(self.condition_list.keys())
                    self.logger.info(f"📋 사용 가능한 조건식: {available}")
                    return []
                
                condition_index = self.condition_list[condition_name]
                self.logger.info(f"🔍 조건식 실행: '{condition_name}' (인덱스: {condition_index})")
                
                # 조건식 실행 시도
                result = self._execute_condition_search(condition_name, condition_index)
                
                if result:
                    self.logger.info(f"✅ 조건식 검색 성공: {len(result)}개 종목 (시도 {attempt + 1})")
                    return result
                else:
                    self.logger.warning(f"⚠️ 조건식 검색 결과 없음 (시도 {attempt + 1})")
                    if attempt < max_retries - 1:
                        self.logger.info("🔄 3초 후 재시도...")
                        time.sleep(3)
                        continue
                
            except Exception as e:
                self.logger.error(f"❌ 조건식 검색 중 오류 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    self.logger.info("🔄 3초 후 재시도...")
                    time.sleep(3)
                    continue
                else:
                    import traceback
                    self.logger.error(traceback.format_exc())
        
        self.logger.error(f"❌ {max_retries}번 시도 후 조건식 검색 실패")
        return []
    
    def _execute_condition_search(self, condition_name: str, condition_index: int) -> List[str]:
        """조건식 검색 실행"""
        try:
            # 이전 결과 초기화
            self.condition_data[condition_name] = []
            
            # 동적 화면번호 생성 (중복 방지)
            import random
            screen_no = str(3000 + random.randint(1, 999))
            
            self.logger.info(f"📡 조건식 실행 요청:")
            self.logger.info(f"  - 화면번호: {screen_no}")
            self.logger.info(f"  - 조건명: {condition_name}")
            self.logger.info(f"  - 조건인덱스: {condition_index}")
            
            # 조건식 실행 전 잠시 대기 (API 안정성)
            time.sleep(0.5)
            
            # 조건식 실행 - OnReceiveTrCondition 이벤트 발생
            ret = self.ocx.SendCondition(
                screen_no,           # 동적 화면번호
                condition_name,      # 조건명
                condition_index,     # 조건인덱스
                0                   # 0: 단순조회, 1: 실시간 조회
            )
            
            if ret == 1:
                self.logger.info("✅ 조건식 실행 요청 성공 - 결과 대기 중...")
                
                # 결과 대기 및 이벤트 처리
                timeout = 0
                max_wait = 20  # 20초로 증가
                result_received = False
                
                while timeout < max_wait:
                    if hasattr(self, 'app') and self.app:
                        self.app.processEvents()  # Qt 이벤트 처리
                    
                    # 결과가 도착했는지 확인
                    if condition_name in self.condition_data:
                        stocks = self.condition_data[condition_name]
                        if isinstance(stocks, list):  # 리스트가 설정되었는지 확인
                            result_received = True
                            self.logger.info(f"📡 결과 수신 완료: {timeout:.1f}초 후, {len(stocks)}개 종목")
                            break
                    
                    if timeout % 3 == 0:  # 3초마다 로그
                        self.logger.debug(f"⏳ 대기 중... {timeout:.1f}/{max_wait}초")
                    
                    time.sleep(0.5)
                    timeout += 0.5
                
                # 최종 결과 반환
                stock_codes = self.condition_data.get(condition_name, [])
                
                if stock_codes:
                    self.logger.info(f"✅ 조건식 '{condition_name}'에서 {len(stock_codes)}개 종목 발견")
                    
                    # 종목 수 제한 (10개로 고정)
                    limited_stocks = stock_codes[:10]
                    
                    if len(stock_codes) > 10:
                        self.logger.info(f"📊 10개 종목으로 제한 (전체: {len(stock_codes)}개)")
                    
                    # 처음 몇 개 종목 로그 출력
                    sample_stocks = limited_stocks[:5]
                    self.logger.info(f"📈 검색된 종목 예시: {sample_stocks}")
                    
                    return limited_stocks
                else:
                    self.logger.warning(f"⚠️ 조건식 '{condition_name}'에 해당하는 종목이 없습니다")
                    return []
            else:
                self.logger.error(f"❌ 조건식 '{condition_name}' 실행 요청 실패")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ 조건식 검색 실행 중 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []
    
    def get_stock_info(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """Get detailed stock information with real-time data"""
        if not self.connected:
            self.logger.error("❌ Not connected to Kiwoom server")
            return {}
        
        stock_info = {}
        
        try:
            # Check market hours first
            market_status = self._get_market_status()
            self.logger.info(f"📊 Market Status: {market_status}")
            
            for i, stock_code in enumerate(stock_codes, 1):
                self.logger.info(f"📊 종목 정보 수집 중 ({i}/{len(stock_codes)}): {stock_code}")
                
                try:
                    # 기본 정보 수집
                    stock_name = self.ocx.GetMasterCodeName(stock_code).strip()
                    
                    if not stock_name:
                        stock_name = f"종목_{stock_code}"
                        self.logger.warning(f"⚠️ 종목명 조회 실패: {stock_code} -> {stock_name}")
                    
                    # Get real-time stock data using TR request
                    realtime_info = self._get_realtime_stock_info(stock_code)
                    
                    # 상세 시장 정보 수집 (Master API)
                    try:
                        detailed_info = self._get_detailed_stock_info(stock_code)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to get detailed info for {stock_code}: {e}")
                        detailed_info = {}  # 빈 딕셔너리로 초기화
                    
                    # Merge realtime and detailed info, prioritizing realtime data
                    if realtime_info:
                        combined_info = {**detailed_info, **realtime_info}
                    else:
                        combined_info = detailed_info
                    
                    # Try to get price data but don't filter out stocks if it fails
                    current_price = combined_info.get('current_price', 0)
                    if not current_price or current_price <= 0:
                        # Try one more fallback with Master API directly
                        try:
                            fallback_price = self.ocx.GetMasterLastPrice(stock_code)
                            if fallback_price:
                                fallback_price = self._clean_number(fallback_price)
                                if fallback_price > 0:
                                    combined_info['current_price'] = fallback_price
                                    combined_info['data_source'] = 'master_fallback'
                                    current_price = fallback_price
                                    self.logger.info(f"✅ Master fallback success for {stock_code}: {fallback_price:,}원")
                        except Exception as fallback_error:
                            self.logger.debug(f"Fallback failed: {fallback_error}")
                    
                    # Show all stocks regardless of price data availability
                    if not current_price or current_price <= 0:
                        self.logger.info(f"📊 {stock_code} 가격 데이터 없음 - 종목 포함 (가격: 0원)")
                        combined_info['current_price'] = 0
                        combined_info['data_source'] = 'no_data'
                    
                    # Calculate market cap if we have price and shares
                    if combined_info.get('current_price') and combined_info.get('listed_shares'):
                        market_cap = combined_info['current_price'] * combined_info['listed_shares']
                        combined_info['market_cap'] = market_cap
                    
                    # Add market status
                    combined_info['market_status'] = market_status
                    
                    # 결과 저장 (오직 유효한 가격 데이터가 있는 종목만)
                    stock_info[stock_code] = {
                        'name': stock_name,
                        'code': stock_code,
                        'timestamp': datetime.now().isoformat(),
                        **combined_info
                    }
                    
                    price_display = f"{current_price:,}원"
                    volume_display = combined_info.get('volume', 0)
                    if isinstance(volume_display, (int, float)) and volume_display > 0:
                        volume_display = f"{volume_display:,}주"
                    else:
                        volume_display = "거래량 정보 없음"
                    
                    self.logger.info(f"  ✅ {stock_name} ({stock_code})")
                    self.logger.info(f"    현재가: {price_display}, 거래량: {volume_display}")
                    self.logger.info(f"    시가총액: {self._format_market_cap(combined_info.get('market_cap', 0))}")
                    
                except Exception as stock_error:
                    self.logger.warning(f"⚠️ 종목 {stock_code} 정보 수집 실패 - 제외: {stock_error}")
                    import traceback
                    self.logger.debug(traceback.format_exc())
                    # 실패한 종목은 결과에 포함하지 않음
                    continue
                
                # API 요청 간격 조정
                time.sleep(0.3)
                    
        except Exception as e:
            self.logger.error(f"❌ 종목 정보 수집 중 전체 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        
        self.logger.info(f"📊 총 {len(stock_info)}개 종목 정보 수집 완료")
        return stock_info
    

    def _get_detailed_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """Get comprehensive stock information using Kiwoom Master API and TR requests"""
        detailed_info = {}  # 초기화 필수!
        
        try:
            # 1. opt10001 TR로 기본 정보 가져오기 (상장주식수 포함)
            basic_info = self._get_stock_basic_info_tr(stock_code)
            if basic_info:
                detailed_info.update(basic_info)
                self.logger.debug(f"{stock_code} TR 정보 수집 성공")
            
            # 2. Master API로 보완 정보 수집
            master_info = self._get_master_stock_info(stock_code)
            if master_info:
                # TR 정보 우선, Master 정보로 보완
                for key, value in master_info.items():
                    if key not in detailed_info or detailed_info[key] == 0:
                        detailed_info[key] = value
            
            # 3. 시가총액 계산
            current_price = detailed_info.get('current_price', 0)
            listed_shares = detailed_info.get('listed_shares', 0)
            
            if current_price > 0 and listed_shares > 0:
                market_cap = current_price * listed_shares
                detailed_info['market_cap'] = market_cap
                
                # 시가총액 등급 계산
                if market_cap >= 10_000_000_000_000:  # 10조 이상
                    detailed_info['market_cap_grade'] = '대형주'
                elif market_cap >= 1_000_000_000_000:  # 1조 이상
                    detailed_info['market_cap_grade'] = '중형주'
                else:
                    detailed_info['market_cap_grade'] = '소형주'
                
                self.logger.info(f"✅ {stock_code} 시가총액: {self._format_market_cap(market_cap)} ({detailed_info['market_cap_grade']})")
            else:
                detailed_info['market_cap'] = 0
                detailed_info['market_cap_grade'] = '정보없음'
                self.logger.warning(f"⚠️ {stock_code} 시가총액 계산 불가 - 현재가: {current_price:,}원, 상장주식수: {listed_shares:,}주")
            
            return detailed_info
            
        except Exception as e:
            self.logger.error(f"❌ 종목 {stock_code} 상세 정보 수집 실패: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return {}

    def _get_stock_basic_info_tr(self, stock_code: str) -> Dict[str, Any]:
        """opt10001 TR로 주식 기본 정보 조회 (상장주식수 포함)"""
        try:
            self.logger.debug(f"🔍 opt10001 TR 요청: {stock_code}")
            
            # TR 데이터 초기화
            self.tr_data = None
            
            # opt10001: 주식기본정보요청
            self.ocx.SetInputValue("종목코드", stock_code)
            
            # 동적 화면번호 생성
            import random
            screen_no = str(8000 + random.randint(1, 999))
            
            # TR 요청
            ret = self.ocx.CommRqData("opt10001_req", "opt10001", 0, screen_no)
            
            if ret != 0:
                self.logger.warning(f"⚠️ opt10001 요청 실패: {ret}")
                return {}
            
            # 응답 대기
            timeout = 0
            max_wait = 10
            
            while timeout < max_wait:
                if hasattr(self, 'app') and self.app:
                    self.app.processEvents()
                
                # TR 데이터가 수신되었는지 확인
                if hasattr(self, 'tr_data') and self.tr_data:
                    break
                    
                time.sleep(0.2)
                timeout += 0.2
            
            if not hasattr(self, 'tr_data') or not self.tr_data:
                self.logger.warning(f"⚠️ opt10001 응답 타임아웃: {stock_code}")
                return {}
            
            # 데이터 파싱
            basic_info = {}
            
            # 현재가
            current_price = self._clean_number(self.tr_data.get('현재가', '0'))
            if current_price > 0:
                basic_info['current_price'] = current_price
            
            # 상장주식수 (단위: 천주 → 주로 변환)
            listed_shares_k = self._clean_number(self.tr_data.get('상장주식', '0'))
            if listed_shares_k > 0:
                basic_info['listed_shares'] = listed_shares_k * 1000  # 천주 → 주
                self.logger.debug(f"✅ {stock_code} 상장주식수: {basic_info['listed_shares']:,}주")
            
            # 시가총액 (단위: 억원 → 원으로 변환)
            market_cap_100m = self._clean_number(self.tr_data.get('시가총액', '0'))
            if market_cap_100m > 0:
                basic_info['market_cap_from_tr'] = market_cap_100m * 100_000_000  # 억원 → 원
            
            # 기타 유용한 정보들
            basic_info['volume'] = self._clean_number(self.tr_data.get('거래량', '0'))
            basic_info['per'] = self._parse_float(self.tr_data.get('PER', '0'))
            basic_info['pbr'] = self._parse_float(self.tr_data.get('PBR', '0'))
            basic_info['eps'] = self._clean_number(self.tr_data.get('EPS', '0'))
            basic_info['bps'] = self._clean_number(self.tr_data.get('BPS', '0'))
            basic_info['roe'] = self._parse_float(self.tr_data.get('ROE', '0'))
            
            # 가격 정보
            basic_info['open_price'] = self._clean_number(self.tr_data.get('시가', '0'))
            basic_info['high_price'] = self._clean_number(self.tr_data.get('고가', '0'))
            basic_info['low_price'] = self._clean_number(self.tr_data.get('저가', '0'))
            basic_info['prev_close'] = self._clean_number(self.tr_data.get('기준가', '0'))
            
            # 등락률 계산
            change_rate = self._parse_float(self.tr_data.get('등락율', '0'))
            basic_info['change_rate'] = change_rate
            
            self.logger.debug(f"✅ opt10001 파싱 완료: {len(basic_info)}개 필드")
            return basic_info
            
        except Exception as e:
            self.logger.warning(f"⚠️ opt10001 TR 처리 실패: {e}")
            return {}

    def _get_master_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """Master API로 보완 정보 수집"""
        master_info = {}
        
        try:
            # 현재가 (TR에서 실패한 경우의 fallback)
            if not master_info.get('current_price'):
                current_price = self.ocx.GetMasterLastPrice(stock_code)
                if current_price:
                    master_info['current_price'] = self._clean_number(current_price)
            
            # 시장 구분
            try:
                market_gubun = self.ocx.GetMasterStockState(stock_code)
                if market_gubun and market_gubun.strip():
                    market_code = market_gubun.strip()
                    if market_code.startswith('0') or market_code == '':
                        master_info['market_type'] = 'KOSPI'
                    else:
                        master_info['market_type'] = 'KOSDAQ'
                else:
                    # 코드 범위로 추정
                    if stock_code.startswith(('00', '01', '02', '03', '04', '05')):
                        master_info['market_type'] = 'KOSPI'
                    else:
                        master_info['market_type'] = 'KOSDAQ'
            except Exception:
                master_info['market_type'] = 'UNKNOWN'
            
            # 거래량 (TR에서 실패한 경우의 fallback)
            if not master_info.get('volume'):
                try:
                    volume = self.ocx.GetMasterVolume(stock_code)
                    if volume:
                        master_info['volume'] = self._clean_number(volume)
                except Exception:
                    pass
            
            return master_info
            
        except Exception as e:
            self.logger.debug(f"Master 정보 수집 오류: {e}")
            return {}

    def _handle_realtime_stock_data(self, trcode: str, record_name: str):
        """Handle real-time stock data from opt10001"""
        try:
            # opt10001 응답 처리
            if trcode == "opt10001":
                self.tr_data = {}
                
                # 모든 필드 추출 (키움 API 필드명 사용)
                fields = [
                    '종목코드', '종목명', '현재가', '거래량', '거래대금',
                    '시가', '고가', '저가', '기준가', '전일대비', '등락율',
                    '상장주식', '시가총액', 'PER', 'PBR', 'EPS', 'BPS', 'ROE',
                    '액면가', '자본금', '신용비율', '연중최고', '연중최저'
                ]
                
                for field in fields:
                    try:
                        value = self.ocx.GetCommData(trcode, record_name, 0, field).strip()
                        if value:
                            self.tr_data[field] = value
                    except Exception:
                        continue
                
                self.logger.debug(f"📡 opt10001 데이터 수신: {len(self.tr_data)}개 필드")
                
        except Exception as e:
            self.logger.error(f"❌ opt10001 데이터 처리 오류: {e}")
            self.tr_data = {}

    def _parse_float(self, value: str) -> float:
        """문자열을 float로 변환"""
        try:
            if not value or value.strip() == "":
                return 0.0
            
            cleaned = value.strip()
            if cleaned.startswith(('+', '-')):
                cleaned = cleaned[1:] if cleaned.startswith('+') else cleaned
            
            cleaned = cleaned.replace(',', '').replace(' ', '')
            
            if cleaned == "" or cleaned == "0":
                return 0.0
                
            return float(cleaned)
            
        except (ValueError, TypeError):
            return 0.0
    
    def _get_market_status(self) -> str:
        """Check if market is open or closed using KST timezone"""
        try:
            import pytz
            from datetime import datetime, time
            
            # Get current time in KST (Korea Standard Time)
            kst = pytz.timezone('Asia/Seoul')
            now_kst = datetime.now(kst)
            current_time = now_kst.time()
            weekday = now_kst.weekday()  # 0=Monday, 6=Sunday
            
            self.logger.debug(f"Current KST time: {now_kst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Weekend check
            if weekday >= 5:  # Saturday=5, Sunday=6
                return "주말 휴장"
            
            # Trading hours: 9:00 AM - 3:30 PM (KST)
            market_open = time(9, 0)
            market_close = time(15, 30)
            
            if market_open <= current_time <= market_close:
                return "정규장 거래중"
            elif current_time < market_open:
                return "장 시작 전"
            else:
                return "장 마감"
                
        except ImportError:
            # Fallback without pytz if not available
            self.logger.warning("⚠️ pytz not available, using system time (may not be accurate for KST)")
            from datetime import datetime, time
            
            now = datetime.now()
            current_time = now.time()
            weekday = now.weekday()
            
            if weekday >= 5:
                return "주말 휴장"
            
            market_open = time(9, 0)
            market_close = time(15, 30)
            
            if market_open <= current_time <= market_close:
                return "정규장 거래중"
            elif current_time < market_open:
                return "장 시작 전"
            else:
                return "장 마감"
                
        except Exception as e:
            self.logger.error(f"❌ Market status check failed: {e}")
            return "상태 확인 불가"
    
    def _get_realtime_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """Get stock information using multiple fallback methods"""
        try:
            # Skip complex TR requests and go directly to reliable Master API
            self.logger.info(f"🔍 Getting stock info for {stock_code}")
            
            # Method 1: Try Master API directly (most reliable)
            closing_info = self._get_closing_price(stock_code)
            
            if closing_info and closing_info.get('current_price', 0) > 0:
                self.logger.info(f"✅ Price data success for {stock_code}: {closing_info.get('current_price', 0):,}원")
                return closing_info
            
            # Method 2: Direct Master API call as final fallback
            try:
                self.logger.info(f"🔄 Direct Master API for {stock_code}")
                last_price = self.ocx.GetMasterLastPrice(stock_code)
                
                if last_price:
                    last_price = self._clean_number(last_price)
                    if last_price > 0:
                        market_status = self._get_market_status()
                        
                        basic_info = {
                            'current_price': last_price,
                            'volume': 0,  # No volume data available
                            'change_rate': 0,  # Cannot calculate without prev data
                            'data_source': 'master_direct',
                            'market_status': market_status,
                            'is_closing_price': market_status in ['장 마감', '주말 휴장', '장 시작 전'],
                            'price_type': '종가' if market_status == '장 마감' else '전일종가' if market_status in ['주말 휴장', '장 시작 전'] else '현재가',
                            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        self.logger.info(f"✅ Direct Master API success for {stock_code}: {last_price:,}원")
                        return basic_info
                        
            except Exception as direct_error:
                self.logger.debug(f"Direct Master API failed: {direct_error}")
            
            # If all methods fail, return None
            self.logger.warning(f"⚠️ All price retrieval methods failed for {stock_code}")
            return None
                
        except Exception as e:
            self.logger.error(f"❌ Complete failure for {stock_code}: {e}")
            return None
    
    def _get_closing_price(self, stock_code: str) -> Dict[str, Any]:
        """Get latest closing price using simplified direct approach"""
        try:
            market_status = self._get_market_status()
            self.logger.info(f"📊 Getting closing price for {stock_code}, market status: {market_status}")
            
            closing_info = {}
            
            # Method 1: Try Master API first (faster and more reliable)
            try:
                self.logger.info(f"🔍 Trying Master API for {stock_code}")
                last_price = self.ocx.GetMasterLastPrice(stock_code)
                
                if last_price:
                    last_price = self._clean_number(last_price)
                    if last_price > 0:
                        closing_info['current_price'] = last_price
                        
                        # Try to get volume data
                        try:
                            # Method 1: 마스터 API로 거래량 시도
                            volume = self.ocx.GetMasterVolume(stock_code)
                            if volume:
                                detailed_info['volume'] = self._clean_number(volume)
                            else:
                                # Method 2: 실시간 데이터로 거래량 시도
                                try:
                                    # 실시간 거래량 조회 (FID 13)
                                    real_volume = self.ocx.GetCommRealData(stock_code, 13)
                                    if real_volume:
                                        detailed_info['volume'] = self._clean_number(real_volume)
                                    else:
                                        detailed_info['volume'] = 0
                                except:
                                    detailed_info['volume'] = 0
                        except Exception:
                            detailed_info['volume'] = 0
                        
                        # Set price type based on market status
                        if market_status == '장 마감':
                            closing_info['is_closing_price'] = True
                            closing_info['price_type'] = '종가'
                        elif market_status == '주말 휴장':
                            closing_info['is_closing_price'] = True
                            closing_info['price_type'] = '전일종가'
                        elif market_status == '장 시작 전':
                            closing_info['is_closing_price'] = True
                            closing_info['price_type'] = '전일종가'
                        else:
                            closing_info['is_closing_price'] = False
                            closing_info['price_type'] = '현재가'
                        
                        closing_info['change_rate'] = 0  # Will be calculated later if needed
                        closing_info['data_source'] = 'master_api'
                        closing_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        self.logger.info(f"✅ Master API success - {stock_code}: {last_price:,}원")
                        return closing_info
                
            except Exception as master_error:
                self.logger.warning(f"⚠️ Master API failed for {stock_code}: {master_error}")
            
            # Method 2: Try chart data as fallback
            try:
                self.logger.info(f"📈 Trying chart data for {stock_code}")
                chart_data = self.get_stock_chart_data(stock_code, "D", 3)
                
                if not chart_data.empty and len(chart_data) >= 1:
                    latest_data = chart_data.iloc[-1]
                    today_close = int(latest_data['close'])
                    
                    if today_close > 0:
                        closing_info['current_price'] = today_close
                        closing_info['volume'] = int(latest_data['volume'])
                        closing_info['high_price'] = int(latest_data['high'])
                        closing_info['low_price'] = int(latest_data['low'])
                        closing_info['open_price'] = int(latest_data['open'])
                        
                        # Calculate change if we have previous data
                        if len(chart_data) >= 2:
                            prev_close = int(chart_data.iloc[-2]['close'])
                            if prev_close > 0:
                                change_amount = today_close - prev_close
                                change_rate = (change_amount / prev_close) * 100
                                closing_info['prev_close'] = prev_close
                                closing_info['change_amount'] = change_amount
                                closing_info['change_rate'] = round(change_rate, 2)
                        
                        # Set price type
                        if market_status == '장 마감':
                            closing_info['is_closing_price'] = True
                            closing_info['price_type'] = '종가'
                        elif market_status == '주말 휴장':
                            closing_info['is_closing_price'] = True
                            closing_info['price_type'] = '전일종가'
                        elif market_status == '장 시작 전':
                            closing_info['is_closing_price'] = True
                            closing_info['price_type'] = '전일종가'
                        else:
                            closing_info['is_closing_price'] = False
                            closing_info['price_type'] = '현재가'
                        
                        closing_info['data_source'] = 'chart_data'
                        closing_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        self.logger.info(f"✅ Chart data success - {stock_code}: {today_close:,}원")
                        return closing_info
                        
            except Exception as chart_error:
                self.logger.warning(f"⚠️ Chart data failed for {stock_code}: {chart_error}")
            
            # If completely failed to get price data, return None
            self.logger.error(f"❌ Complete failure to get price data for {stock_code}")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Closing price retrieval completely failed for {stock_code}: {e}")
            return None
    
    def _format_market_cap(self, market_cap: int) -> str:
        """Format market cap for display"""
        if not market_cap or market_cap == 0:
            return "N/A"
        
        try:
            if market_cap >= 1000000000000:  # 조 단위
                return f"{market_cap/1000000000000:.1f}조원"
            elif market_cap >= 100000000:  # 억 단위
                return f"{market_cap/100000000:.0f}억원"
            elif market_cap >= 10000:  # 만 단위
                return f"{market_cap/10000:.0f}만원"
            else:
                return f"{market_cap:,.0f}원"
        except:
            return "N/A"
    
    def _clean_number(self, value: str) -> int:
        """Clean and convert number string to integer"""
        if not value or value.strip() == "":
            return 0
        
        try:
            # 키움 데이터는 보통 부호가 앞에 붙음 (+, -, 공백)
            cleaned = value.strip()
            
            # 부호 제거 및 콤마 제거
            if cleaned.startswith(('+', '-')):
                cleaned = cleaned[1:]
            
            cleaned = cleaned.replace(',', '').replace(' ', '')
            
            if cleaned == "" or cleaned == "0":
                return 0
                
            return int(float(cleaned))  # float을 거쳐서 소수점 처리
            
        except (ValueError, TypeError) as e:
            self.logger.debug(f"숫자 변환 실패: '{value}' -> {e}")
            return 0
    
    # Event handlers
    def _on_event_connect(self, err_code):
        """Handle connection event"""
        if err_code == 0:
            self.connected = True
            self.logger.info("✅ Login successful")
        else:
            self.connected = False
            self.logger.error(f"❌ Login failed with error code: {err_code}")
        
        if self.login_loop:
            self.login_loop.exit()
    
    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, prev_next):
        """Handle TR data reception"""
        self.logger.debug(f"📡 TR 데이터 수신: {rqname}, 화면번호: {screen_no}")
        
        try:
            if rqname == "opt10081_req":  # Daily chart data
                self._handle_daily_chart_data(trcode, record_name)
            elif rqname == "opt10080_req":  # Minute chart data
                self._handle_minute_chart_data(trcode, record_name)
            elif rqname == "opt10001_req":  # Real-time stock data
                self._handle_realtime_stock_data(trcode, record_name)
        except Exception as e:
            self.logger.error(f"❌ TR data handling error: {e}")
        
        if self.data_loop:
            self.data_loop.exit()
    
    def _on_receive_real_data(self, stock_code, real_type, real_data):
        """Handle real-time data"""
        self.logger.debug(f"📡 Real-time data: {stock_code}")
    
    def _on_receive_condition_ver(self, ret, msg):
        """Handle condition version event - 조건식 버전 이벤트"""
        if ret == 1:
            self.condition_loaded = True
            self.logger.info(f"✅ 조건식 버전 로드 성공: {msg}")
        else:
            self.condition_loaded = False
            self.logger.error(f"❌ 조건식 버전 로드 실패: {msg}")
            
        # 추가 디버깅 정보
        self.logger.debug(f"조건식 로드 상태: {self.condition_loaded}")
    
    def _on_receive_tr_condition(self, screen_no, code_list, condition_name, condition_index, inquiry):
        """Handle condition screening results - triggered when SendCondition() is called"""
        self.logger.info(f"📡 OnReceiveTrCondition 이벤트 수신:")
        self.logger.info(f"  - screen_no: {screen_no}")
        self.logger.info(f"  - condition_name: {condition_name}")
        self.logger.info(f"  - condition_index: {condition_index}")
        self.logger.info(f"  - inquiry: {inquiry}")
        self.logger.info(f"  - code_list 길이: {len(code_list) if code_list else 0}")
        
        # code_list 상세 분석
        if code_list:
            self.logger.info(f"  - code_list 원본 (처음 100자): {repr(code_list[:100])}")
            
            # 세미콜론으로 분리
            all_parts = code_list.split(';')
            self.logger.info(f"  - 세미콜론 분리 결과: {len(all_parts)}개 파트")
            
            # 빈 문자열 제거
            stocks = [s.strip() for s in all_parts if s.strip()]
            self.condition_data[condition_name] = stocks
            
            self.logger.info(f"✅ 조건식 '{condition_name}' 결과: {len(stocks)}개 종목")
            
            # 처음 몇 개 종목 로깅
            if stocks:
                sample_count = min(5, len(stocks))
                sample_stocks = stocks[:sample_count]
                self.logger.info(f"📈 검색된 종목 (처음 {sample_count}개): {sample_stocks}")
            else:
                self.logger.warning("⚠️ 파싱 후에도 종목이 없음")
        else:
            self.condition_data[condition_name] = []
            self.logger.warning(f"⚠️ 조건식 '{condition_name}' 결과: code_list가 비어있음 또는 None")
    
    def _on_receive_real_condition(self, stock_code, condition_type, condition_name, condition_index):
        """Handle real-time condition events - for real-time condition monitoring"""
        self.logger.debug(f"📡 Real-time condition event: {stock_code}, type={condition_type}, condition={condition_name}")
        
        # condition_type: 'I' = 편입, 'D' = 이탈
        if condition_type == 'I':
            self.logger.info(f"📈 Stock {stock_code} entered condition '{condition_name}'")
        elif condition_type == 'D':
            self.logger.info(f"📉 Stock {stock_code} exited condition '{condition_name}'")
    
    def is_connected(self) -> bool:
        """Check if connected to Kiwoom server"""
        return self.connected
    
    def get_account_list(self) -> List[str]:
        """Get account list"""
        if not self.connected:
            return []
        
        try:
            account_list = self.ocx.GetLoginInfo("ACCNO")
            return account_list.split(';')[:-1] if account_list else []
        except Exception as e:
            self.logger.error(f"❌ Error getting account list: {e}")
            return []
    
    def debug_condition_info(self):
        """조건식 정보 디버깅 출력"""
        try:
            self.logger.info("🔍 조건식 디버깅 정보:")
            self.logger.info(f"  - 연결 상태: {self.connected}")
            self.logger.info(f"  - 조건식 로드 상태: {getattr(self, 'condition_loaded', False)}")
            self.logger.info(f"  - 저장된 조건식 수: {len(getattr(self, 'condition_list', {}))}")
            
            if hasattr(self, 'condition_list') and self.condition_list:
                self.logger.info("  - 조건식 목록:")
                for name, index in self.condition_list.items():
                    self.logger.info(f"    * {name} (인덱스: {index})")
            else:
                self.logger.info("  - 조건식 목록: 없음")
                
            # 목표 조건식 확인
            target = config.kiwoom.screening_condition
            self.logger.info(f"  - 목표 조건식: '{target}'")
            
            if hasattr(self, 'condition_list') and target in self.condition_list:
                self.logger.info(f"  - 목표 조건식 상태: ✅ 발견됨 (인덱스: {self.condition_list[target]})")
            else:
                self.logger.info(f"  - 목표 조건식 상태: ❌ 없음")
                
        except Exception as e:
            self.logger.error(f"❌ 디버깅 정보 출력 중 오류: {e}")
    
    def force_refresh_conditions(self):
        """조건식 강제 새로고침"""
        try:
            self.logger.info("🔄 조건식 강제 새로고침...")
            
            # 기존 데이터 초기화
            self.condition_list = {}
            self.condition_data = {}
            self.condition_loaded = False
            
            # 조건식 다시 로드
            return self.load_condition_list()
            
        except Exception as e:
            self.logger.error(f"❌ 조건식 새로고침 중 오류: {e}")
            return False
    
    def get_stock_chart_data(self, stock_code: str, period: str = "D", count: int = 100) -> pd.DataFrame:
        """
        Get historical price data for technical analysis
        
        Args:
            stock_code: Stock code (e.g., '005930')
            period: Chart period ('D' for daily, 'm' for minute)
            count: Number of data points to retrieve (max 600)
            
        Returns:
            DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume']
        """
        if not self.connected:
            self.logger.error("❌ Not connected to Kiwoom API")
            return pd.DataFrame()
        
        try:
            self.logger.info(f"📊 Requesting {period} chart data for {stock_code} ({count} bars)")
            
            # Prepare request
            self.chart_data = []  # Reset chart data
            
            if period.upper() == "D":
                # Daily chart data (opt10081)
                self.ocx.SetInputValue("종목코드", stock_code)
                self.ocx.SetInputValue("기준일자", "")  # Today
                self.ocx.SetInputValue("수정주가구분", "1")  # Adjusted price
                
                # Request data
                ret = self.ocx.CommRqData("opt10081_req", "opt10081", 0, "0001")
                
            elif period.upper() == "M":
                # Minute chart data (opt10080)
                self.ocx.SetInputValue("종목코드", stock_code)
                self.ocx.SetInputValue("틱범위", "1")  # 1-minute
                self.ocx.SetInputValue("수정주가구분", "1")
                
                # Request data
                ret = self.ocx.CommRqData("opt10080_req", "opt10080", 0, "0002")
            else:
                self.logger.error(f"❌ Unsupported period: {period}")
                return pd.DataFrame()
            
            if ret != 0:
                self.logger.error(f"❌ Chart data request failed: {ret}")
                return pd.DataFrame()
            
            # Wait for data reception
            self.data_loop = QEventLoop()
            self.data_loop.exec_()
            
            # Convert to DataFrame
            if hasattr(self, 'chart_data') and self.chart_data:
                df = pd.DataFrame(self.chart_data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                
                self.logger.info(f"✅ Retrieved {len(df)} data points for {stock_code}")
                return df.tail(count)  # Return latest 'count' rows
            else:
                self.logger.warning(f"⚠️ No chart data received for {stock_code}")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"❌ Error getting chart data for {stock_code}: {e}")
            return pd.DataFrame()
    
    def _handle_daily_chart_data(self, trcode: str, record_name: str):
        """Handle daily chart data from opt10081"""
        try:
            # Get number of data rows
            data_count = self.ocx.GetRepeatCnt(trcode, record_name)
            self.logger.debug(f"📊 Daily chart data count: {data_count}")
            
            chart_data = []
            for i in range(data_count):
                date_str = self.ocx.GetCommData(trcode, record_name, i, "일자").strip()
                open_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, i, "시가"))
                high_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, i, "고가"))
                low_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, i, "저가"))
                close_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, i, "현재가"))
                volume = self._clean_number(self.ocx.GetCommData(trcode, record_name, i, "거래량"))
                
                # Format date
                if len(date_str) == 8:  # YYYYMMDD
                    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                else:
                    formatted_date = date_str
                
                chart_data.append({
                    'date': formatted_date,
                    'open': abs(open_price),  # Remove negative signs
                    'high': abs(high_price),
                    'low': abs(low_price),
                    'close': abs(close_price),
                    'volume': abs(volume)
                })
            
            self.chart_data = chart_data
            self.logger.debug(f"✅ Parsed {len(chart_data)} daily chart records")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling daily chart data: {e}")
            self.chart_data = []
    
    def _handle_minute_chart_data(self, trcode: str, record_name: str):
        """Handle minute chart data from opt10080"""
        try:
            # Get number of data rows
            data_count = self.ocx.GetRepeatCnt(trcode, record_name)
            self.logger.debug(f"📊 Minute chart data count: {data_count}")
            
            chart_data = []
            for i in range(data_count):
                time_str = self.ocx.GetCommData(trcode, record_name, i, "체결시간").strip()
                open_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, i, "시가"))
                high_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, i, "고가"))
                low_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, i, "저가"))
                close_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, i, "현재가"))
                volume = self._clean_number(self.ocx.GetCommData(trcode, record_name, i, "거래량"))
                
                # Format datetime for minute data
                if len(time_str) >= 8:  # YYYYMMDDHHMM or similar
                    if len(time_str) == 8:  # HHMM format
                        # Use today's date with the time
                        today = datetime.now().strftime("%Y-%m-%d")
                        formatted_date = f"{today} {time_str[:2]}:{time_str[2:4]}:00"
                    else:  # Full datetime
                        formatted_date = f"{time_str[:4]}-{time_str[4:6]}-{time_str[6:8]} {time_str[8:10]}:{time_str[10:12]}:00"
                else:
                    formatted_date = time_str
                
                chart_data.append({
                    'date': formatted_date,
                    'open': abs(open_price),
                    'high': abs(high_price),
                    'low': abs(low_price),
                    'close': abs(close_price),
                    'volume': abs(volume)
                })
            
            self.chart_data = chart_data
            self.logger.debug(f"✅ Parsed {len(chart_data)} minute chart records")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling minute chart data: {e}")
            self.chart_data = []
    
    def _handle_realtime_stock_data(self, trcode: str, record_name: str):
        """Handle real-time stock data from opt10001"""
        try:
            # Extract real-time stock information
            current_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, 0, "현재가"))
            volume = self._clean_number(self.ocx.GetCommData(trcode, record_name, 0, "거래량"))
            change_rate = self._clean_number(self.ocx.GetCommData(trcode, record_name, 0, "등락률"))
            change_amount = self._clean_number(self.ocx.GetCommData(trcode, record_name, 0, "전일대비"))
            high_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, 0, "고가"))
            low_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, 0, "저가"))
            open_price = self._clean_number(self.ocx.GetCommData(trcode, record_name, 0, "시가"))
            prev_close = self._clean_number(self.ocx.GetCommData(trcode, record_name, 0, "기준가"))
            
            # Calculate proper change rate if needed
            if current_price > 0 and prev_close > 0 and change_rate == 0:
                change_rate = ((current_price - prev_close) / prev_close) * 100
            
            # Store the data
            self.current_stock_data = {
                'current_price': abs(current_price) if current_price != 0 else 0,
                'volume': abs(volume) if volume != 0 else 0,
                'change_rate': change_rate / 100 if abs(change_rate) > 100 else change_rate,  # Convert percentage
                'change_amount': change_amount,
                'high_price': abs(high_price) if high_price != 0 else 0,
                'low_price': abs(low_price) if low_price != 0 else 0,
                'open_price': abs(open_price) if open_price != 0 else 0,
                'prev_close': abs(prev_close) if prev_close != 0 else 0,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.logger.debug(f"✅ Real-time stock data extracted: {self.current_stock_data}")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling real-time stock data: {e}")
            self.current_stock_data = {}

