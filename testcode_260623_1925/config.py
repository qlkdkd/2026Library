import pandas as pd

# 코드 데이터 경로 설정
DATA_PATH = r'C:\Users\USER\Desktop\develop\공모전\console_test\testcode_260623_1139\datacode_list.xlsx'

# 각 시트 데이터 로드
try:
    region = pd.read_excel(DATA_PATH, sheet_name='지역')
    detail = pd.read_excel(DATA_PATH, sheet_name='세부주제')
    genre = pd.read_excel(DATA_PATH, sheet_name='장르')
    isbn = pd.read_excel(DATA_PATH, sheet_name='ISBN')
    age = pd.read_excel(DATA_PATH, sheet_name='나이')
    sex = pd.read_excel(DATA_PATH, sheet_name='성별')
except Exception as e:
    print(f"[!] 초기 데이터 로드 중 오류 발생 (경로를 확인하세요): {e}")
    region = detail = genre = isbn = age = sex = pd.DataFrame()

# 마스터 데이터 딕셔너리 관리
MASTER_DATA_DICT = {
    "지역": region,
    "세부주제": detail,
    "장르": genre,
    "ISBN": isbn,
    "나이": age,
    "성별": sex
}

# API URL 주소 사전 정의
URL_DICT = {
    '정보공개': 'http://data4library.kr/api/loanItemSrch',
    '도서관별 장서/대출 데이터 조회': 'https://data4library.kr/api/itemSrch',
    '인기대출도서 조회': 'https://data4library.kr/api/loanItemSrch',
    '마니아/다독자를 위한 추천도서 조회': 'https://data4library.kr/api/recommendRecommend'
}