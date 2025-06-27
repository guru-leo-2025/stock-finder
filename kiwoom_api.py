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
        """Get basic stock information - 종목 코드와 이름만 수집"""
        if not self.connected:
            self.logger.error("❌ Not connected to Kiwoom server")
            return {}
        
        stock_info = {}
        
        try:
            for i, stock_code in enumerate(stock_codes, 1):
                self.logger.info(f"📊 종목 정보 수집 중 ({i}/{len(stock_codes)}): {stock_code}")
                
                try:
                    # 종목명 조회 (Master API 사용)
                    stock_name = self.ocx.GetMasterCodeName(stock_code).strip()
                    
                    # 종목명이 없으면 대체명 사용
                    if not stock_name:
                        stock_name = f"종목_{stock_code}"
                        self.logger.warning(f"⚠️ 종목명 조회 실패: {stock_code} -> {stock_name}")
                    
                    # 결과 저장 (코드와 이름만)
                    stock_info[stock_code] = {
                        'name': stock_name,
                        'code': stock_code,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    self.logger.info(f"  ✅ {stock_name} ({stock_code})")
                    
                except Exception as stock_error:
                    self.logger.warning(f"⚠️ 종목 {stock_code} 정보 수집 실패: {stock_error}")
                    
                    # 실패해도 기본 정보는 저장
                    stock_info[stock_code] = {
                        'name': f"종목_{stock_code}",
                        'code': stock_code,
                        'timestamp': datetime.now().isoformat()
                    }
                
                # 빠른 처리를 위해 대기시간 단축
                time.sleep(0.1)
                    
        except Exception as e:
            self.logger.error(f"❌ 종목 정보 수집 중 전체 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        
        self.logger.info(f"📊 총 {len(stock_info)}개 종목 정보 수집 완료")
        return stock_info
    
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

# Test mode mock class for development
class MockKiwoomAPI:
    """Mock Kiwoom API for testing without actual connection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("🧪 Using Mock Kiwoom API (Test Mode)")
        self.connected = True
    
    def connect(self) -> bool:
        self.logger.info("🧪 Mock connection successful")
        return True
    
    def disconnect(self):
        self.logger.info("🧪 Mock disconnection")
    
    def load_condition_list(self) -> bool:
        self.logger.info("🧪 Mock condition list loaded")
        return True
    
    def get_condition_stocks(self, condition_name: str = None) -> List[str]:
        # Return mock stock codes for testing
        mock_stocks = ["005930", "000660", "035420", "005490", "051910", 
                      "006400", "035720", "105560", "055550", "096770"]
        self.logger.info(f"🧪 Mock condition '{condition_name}' returned {len(mock_stocks)} stocks")
        return mock_stocks[:config.trading.max_stocks]
    
    def get_stock_info(self, stock_codes: List[str]) -> Dict[str, Dict]:
        # Return mock stock information
        mock_names = ["삼성전자", "SK하이닉스", "네이버", "포스코홀딩스", "LG화학",
                     "삼성SDI", "카카오", "KB금융", "신한지주", "엔씨소프트"]
        
        stock_info = {}
        for i, code in enumerate(stock_codes):
            stock_info[code] = {
                'name': mock_names[i] if i < len(mock_names) else f"테스트주식{i}",
                'code': code,
                'current_price': 50000 + (i * 5000),
                'volume': 100000 + (i * 10000),
                'timestamp': datetime.now().isoformat()
            }
        
        self.logger.info(f"🧪 Mock stock info for {len(stock_codes)} stocks")
        return stock_info
    
    def is_connected(self) -> bool:
        return True
    
    def get_account_list(self) -> List[str]:
        return ["8888888-88"]