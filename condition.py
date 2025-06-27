import sys
import os
import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
import pythoncom
import time

class KiwoomAPI(QAxWidget):
    def __init__(self):
        super().__init__()
        self.ocx_name = "KHOPENAPI.KHOpenAPICtrl.1"
        self.setControl(self.ocx_name)
        
        # 로그 설정
        self.setup_logging()
        
        # 이벤트 슬롯 연결
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveConditionVer.connect(self.condition_slot)
        
        # 로그인 상태 변수
        self.login_status = False
        self.condition_loaded = False
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('kiwoom_api.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def comm_connect(self):
        """키움증권 로그인"""
        self.logger.info("키움증권 로그인 시도...")
        self.dynamicCall("CommConnect()")
        
        # 로그인 완료까지 대기
        loop = QEventLoop()
        self.login_event_loop = loop
        loop.exec_()
        
    def login_slot(self, err_code):
        """로그인 이벤트 슬롯"""
        if err_code == 0:
            self.login_status = True
            self.logger.info("로그인 성공!")
            self.get_user_info()
            self.load_condition_list()
        else:
            self.login_status = False
            self.logger.error(f"로그인 실패. 오류코드: {err_code}")
            
        if hasattr(self, 'login_event_loop'):
            self.login_event_loop.exit()
            
    def get_user_info(self):
        """사용자 정보 조회"""
        user_id = self.dynamicCall("GetLoginInfo(QString)", "USER_ID")
        user_name = self.dynamicCall("GetLoginInfo(QString)", "USER_NAME")
        account_count = self.dynamicCall("GetLoginInfo(QString)", "ACCOUNT_CNT")
        accounts = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        
        self.logger.info(f"사용자 ID: {user_id}")
        self.logger.info(f"사용자 이름: {user_name}")
        self.logger.info(f"보유 계좌수: {account_count}")
        self.logger.info(f"계좌번호: {accounts}")
        
        return {
            'user_id': user_id,
            'user_name': user_name,
            'account_count': account_count,
            'accounts': accounts.split(';')[:-1] if accounts else []
        }
        
    def load_condition_list(self):
        """조건검색식 목록 로드"""
        self.logger.info("조건검색식 목록 로드 중...")
        result = self.dynamicCall("GetConditionLoad()")
        
        if result == 1:
            self.logger.info("조건검색식 로드 요청 성공")
        else:
            self.logger.error("조건검색식 로드 요청 실패")
            
    def condition_slot(self, lRet, sMsg):
        """조건검색식 로드 완료 이벤트 슬롯"""
        self.logger.info(f"조건검색식 로드 결과: {lRet}, 메시지: {sMsg}")
        
        if lRet == 1:
            self.condition_loaded = True
            self.get_condition_name_list()
        else:
            self.logger.error("조건검색식 로드 실패")
            
    def get_condition_name_list(self):
        """조건검색식 목록 조회"""
        condition_name_list = self.dynamicCall("GetConditionNameList()")
        
        if not condition_name_list:
            self.logger.warning("등록된 조건검색식이 없습니다.")
            return []
            
        self.logger.info(f"조건검색식 원본 데이터: {condition_name_list}")
        
        # 조건검색식 파싱
        conditions = []
        condition_list = condition_name_list.split(';')[:-1]  # 마지막 빈 문자열 제거
        
        for condition in condition_list:
            if '^' in condition:
                index, name = condition.split('^')
                conditions.append({
                    'index': int(index),
                    'name': name
                })
                self.logger.info(f"조건검색식 발견 - 인덱스: {index}, 이름: {name}")
                
        return conditions
        
    def send_condition_search(self, condition_index, condition_name):
        """조건검색 실행"""
        self.logger.info(f"조건검색 실행: {condition_name} (인덱스: {condition_index})")
        
        # 조건검색 요청
        # 마지막 파라미터: 0=일반조회, 1=실시간조회
        result = self.dynamicCall(
            "SendCondition(QString, QString, int, int)",
            "0156",  # 화면번호 (임의)
            condition_name,
            condition_index,
            0  # 일반조회
        )
        
        if result == 1:
            self.logger.info("조건검색 요청 성공")
        else:
            self.logger.error("조건검색 요청 실패")
            
        return result


class KiwoomConditionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.kiwoom = KiwoomAPI()
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("키움증권 조건검색식 조회")
        self.setGeometry(100, 100, 800, 600)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 레이아웃
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 로그인 버튼
        self.login_btn = QPushButton("키움증권 로그인")
        self.login_btn.clicked.connect(self.login_kiwoom)
        layout.addWidget(self.login_btn)
        
        # 조건검색식 목록 표시
        self.condition_list = QListWidget()
        layout.addWidget(QLabel("조건검색식 목록:"))
        layout.addWidget(self.condition_list)
        
        # 조건검색 실행 버튼
        self.search_btn = QPushButton("선택된 조건으로 검색 실행")
        self.search_btn.clicked.connect(self.execute_condition_search)
        self.search_btn.setEnabled(False)
        layout.addWidget(self.search_btn)
        
        # 로그 출력 영역
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        layout.addWidget(QLabel("로그:"))
        layout.addWidget(self.log_text)
        
    def login_kiwoom(self):
        """키움증권 로그인 실행"""
        self.login_btn.setEnabled(False)
        self.login_btn.setText("로그인 중...")
        
        try:
            self.kiwoom.comm_connect()
            
            if self.kiwoom.login_status:
                self.login_btn.setText("로그인 완료")
                self.load_conditions()
            else:
                self.login_btn.setText("로그인 실패")
                self.login_btn.setEnabled(True)
                
        except Exception as e:
            self.log_text.append(f"로그인 오류: {str(e)}")
            self.login_btn.setText("로그인")
            self.login_btn.setEnabled(True)
            
    def load_conditions(self):
        """조건검색식 목록 로드"""
        # 조건검색식 로드 완료까지 잠시 대기
        QTimer.singleShot(2000, self.update_condition_list)
        
    def update_condition_list(self):
        """조건검색식 목록 업데이트"""
        if self.kiwoom.condition_loaded:
            conditions = self.kiwoom.get_condition_name_list()
            
            self.condition_list.clear()
            for condition in conditions:
                item_text = f"[{condition['index']}] {condition['name']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, condition)
                self.condition_list.addItem(item)
                
            if conditions:
                self.search_btn.setEnabled(True)
                self.log_text.append(f"총 {len(conditions)}개의 조건검색식을 발견했습니다.")
            else:
                self.log_text.append("등록된 조건검색식이 없습니다.")
        else:
            self.log_text.append("조건검색식 로드가 아직 완료되지 않았습니다.")
            QTimer.singleShot(1000, self.update_condition_list)
            
    def execute_condition_search(self):
        """선택된 조건검색 실행"""
        current_item = self.condition_list.currentItem()
        if current_item:
            condition = current_item.data(Qt.UserRole)
            self.kiwoom.send_condition_search(condition['index'], condition['name'])
            self.log_text.append(f"조건검색 실행: {condition['name']}")
        else:
            self.log_text.append("조건검색식을 선택해주세요.")


def main():
    app = QApplication(sys.argv)
    
    # 키움 OpenAPI는 32bit에서만 동작하므로 확인
    if sys.maxsize > 2**32:
        print("경고: 키움 OpenAPI는 32bit Python에서만 정상 동작합니다.")
        print("32bit Python 환경에서 실행해주세요.")
    
    window = KiwoomConditionApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()