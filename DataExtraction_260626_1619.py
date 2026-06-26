import pandas as pd
import xml.etree.ElementTree as ET
import requests
import requests
from bs4 import BeautifulSoup as bs
from concurrent.futures import ThreadPoolExecutor

class DataCodeSearch:

    # 클래스 내에 사용될 변수들###############3
    def __init__(self):
        self.data_path = './datacode_list.xlsx'
        
        self.region = pd.read_excel(self.data_path, sheet_name='지역')
        self.detail = pd.read_excel(self.data_path, sheet_name='세부주제')
        self.genre = pd.read_excel(self.data_path, sheet_name='장르')
        self.isbn = pd.read_excel(self.data_path, sheet_name='ISBN')
        self.age = pd.read_excel(self.data_path, sheet_name='나이')
        self.sex = pd.read_excel(self.data_path, sheet_name='성별')

        self.master_data_dict = {
            "지역": self.region,
            "세부주제": self.detail,
            "장르": self.genre,
            "ISBN": self.isbn,
            "나이": self.age,
            "성별": self.sex
        }

        self.url_dict = {
            '정보공개':'http://data4library.kr/api/loanItemSrch',
            '도서관별 장서/대출 데이터 조회':'https://data4library.kr/api/itemSrch',
            '인기대출도서 조회':'https://data4library.kr/api/loanItemSrch',
            '마니아/다독자를 위한 추천도서 조회':'https://data4library.kr/api/recommandList',
            '도서상세 조회':'https://data4library.kr/api/srchDtlList',
            '도서 키워드 목록':'https://data4library.kr/api/keywordList',
            '도서별 이용 분석':'https://data4library.kr/api/usageAnalysisList',
            '도서관/지역별 인기대출 도서 조회':'https://data4library.kr/api/loanItemSrchByLib',
            '도서관별 대출반납 추이':'https://data4library.kr/api/usageTrend',
            '도서관별 도서 소장여부 및 대출 가능여부 조회':'https://data4library.kr/api/bookExist',
            '대출 급상승 도서':'https://data4library.kr/api/hotTrend',
            '도서 소장 도서관 조회':'https://data4library.kr/api/libSrchByBook',
            '도서관별 통합정보':'https://data4library.kr/api/extends/libSrch',
            '도서관별 인기대출도서 통합':'https://data4library.kr/api/extends/loanItemSrchByLib',
            '도서 검색':'https://data4library.kr/api/srchBooks',
            '이달의 키워드':'https://data4library.kr/api/monthlyKeywords',
            '지역별 독서량/독서율':'https://data4library.kr/api/readQt',
            '신착도서 조회':'https://data4library.kr/api/newArrivalBook'
        }
    ###############################


    # 마스터 데이터 조회#############333
    def search_master_data(self, category, query):
        """
        작성하신 엑셀 로드 환경에서 시트별로 서로 다른 열 이름을 동적으로 파악하여, 
        '코드값'을 제외한 모든 텍스트 열을 대상으로 검색어(query)를 자동 탐색하는 통합 함수
        """
        # 카테고리(시트명) 유효성 검사
        if category not in self.master_data_dict:
            return f"❌ 존재하지 않는 시트(카테고리)입니다. 선택 가능: {list(self.master_data_dict.keys())}"
        
        # 해당 시트의 데이터프레임 카피 복사
        df = self.master_data_dict[category].copy()
        query = str(query).strip()
        
        # [알고리즘 핵심] '코드값' 열을 제외하고 실제 문자열 데이터가 담긴 열 이름들만 추출
        searchable_columns = [col for col in df.columns if col != '코드값']
        
        if not searchable_columns:
            return "❌ 검색 가능한 데이터 열이 해당 시트에 존재하지 않습니다."
        
        # 모든 대상 열의 데이터를 문자열로 변환한 뒤, 검색어 포함 여부(Boolean Mask)를 누적 계산 (OR 조건)
        condition = df[searchable_columns[0]].astype(str).str.contains(query, na=False)
        for col in searchable_columns[1:]:
            condition |= df[col].astype(str).str.contains(query, na=False)
            
        # 조건에 일치하는 결과 필터링
        matched_result = df[condition]
        
        if matched_result.empty:
            return f"'{query}'에 매핑되는 코드를 [{category}] 시트에서 찾을 수 없습니다."
            
        print(f"\n🔍 [{category}] 시트에서 '{query}' 검색 결과:")
        return matched_result.to_string(index=False)
    ##############################


    # api url에 접근 후, 해당 xml을 데이터프레임으로 변환하는 함수 (페이징 지원 버전)
    def read_xml_by_key(self, api_key, params):
        if api_key not in self.url_dict:
            raise KeyError(f"'{api_key}'은(는) 존재하지 않는 API 키 이름입니다.")
            
        url = self.url_dict[api_key]
        
        # 사용자가 원한 전체 목표 행 개수 확인 (정수 변환)
        target_size = int(params.get('pageSize', 200))
        
        all_dfs = []      # 각 페이지별 데이터프레임을 모을 리스트
        current_page = 1
        collected_rows = 0
        
        print(f"[{api_key}] 총 {target_size}개의 데이터 수집 시작...")

        while collected_rows < target_size:
            # API 1회 요청당 최대 1,000개씩 쪼개서 요청
            req_size = min(1000, target_size - collected_rows)
            
            # 요청 파라미터 복사 및 수정
            req_params = params.copy()
            req_params['pageNo'] = str(current_page)
            req_params['pageSize'] = str(req_size)
            
            # API 호출
            response = requests.get(url, params=req_params)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            root = ET.fromstring(response.text)
            
            parsed_list = []
            for doc in root.findall('.//doc'):
                doc_dict = {}
                for child in doc:
                    doc_dict[child.tag] = child.text
                parsed_list.append(doc_dict)
                
            # 이번 페이지에서 가져온 데이터가 없으면 루프 종료 (데이터 전건 수집 완료 시)
            if not parsed_list:
                break
                
            page_df = pd.DataFrame(parsed_list)
            all_dfs.append(page_df)
            
            collected_rows += len(page_df)
            print(f" -> {current_page}페이지 수집 완료 ({len(page_df)}행, 누적: {collected_rows}/{target_size})")
            
            # 만약 요청한 개수보다 적게 들어왔다면 다음 페이지가 없는 것이므로 종료
            if len(page_df) < req_size:
                break
                
            current_page += 1

        # 수집된 모든 데이터프레임 병합
        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True)
            return final_df
        else:
            return pd.DataFrame() # 빈 데이터프레임 반환
    #################################################
        

    def fetch_single_abstract(self, url):
        try:
            # timeout을 설정하여 먹통이 되는 것을 방지
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            html = bs(response.text, 'html.parser')
            txt = html.find(class_='v_b_abstract')
            
            if txt:
                clean_txt = txt.get_text()
                clean_txt = clean_txt.replace('\n책소개\n', '').replace('\n', '').strip()
                return clean_txt
            else:
                return "개요 정보 없음"
        except Exception as e:
            return f"에러 발생 ({e})"

        
    def extractTxt_fast(self, df):
        urls = df['bookDtlUrl'].tolist()
        names = df['bookname'].tolist()
        
        print(f"[*] 총 {len(urls)}건의 도서 개요 추출 시작 (병렬 처리)...")
        
        # ThreadPoolExecutor를 사용해 동시에 최대 10개의 요청을 보냅니다.
        # 서버에 무리가 가지 않는 선(10~20)에서 숫자를 조절하면 좋습니다.
        with ThreadPoolExecutor(max_workers=10) as executor:
            # executor.map은 순서를 보장하며 함수를 병렬로 실행해 줍니다.
            txt_list = list(executor.map(self.fetch_single_abstract, urls))
            
        print("[+] 모든 도서 개요 추출 완료!")
        
        txt_df = pd.DataFrame({
            'bookname': names,
            'info': txt_list
        })
        
        return txt_df



if __name__ == '__main__':
    dt = DataCodeSearch()
    
    print("\n" + "="*50 + "\n[도서 추천 및 군집화 프로그램 테스트 실행]\n" + "="*50)
    
    sex = input('성별 입력(남성, 여성, 미상): ')
    age = input('나이대 입력(영유아(0~5세),\
                 유아(6~7세), 초등(8~13세), 청소년(14~19세),\
                 20대, ..., 60세 이상, 미상, \
                1, 2학년, 3, 4학년, 5, 6학년, 중등, 고등): ')
    prov_region = input('상위행정구역 이름(특별/광역시, 도): ')
    detail_region = input('세부지역명 입력(시, 군, 구): ')

    # 파라미터 내 변수 입력
    startDt = input('검색시작일자 입력(yyyy-mm-dd 형식으로): ')
    endDt = input('검색종료일자 입력(yyyy-mm-dd 형식으로): ')
    kdc = input('대주제 입력: ')
    #dtl_kdc = input('세부주제 입력: ')
    pageNo = input('페이지 번호 입력(기본값: 1): ')
    pageSize = input('페이지 사이즈 입력(기본값: 200): ')

    # 2. 코드북 데이터 매핑을 통해 API 코드 변환
    sex_code = dt.search_master_data('성별', sex)
    age_code = dt.search_master_data('나이', age)
    region_code = dt.search_master_data('지역', (prov_region, detail_region))

    # api url 접근용 딕셔너리
    params = {
    'authKey': '',  # 도서관정보나루에서 발급받은 Key
    'startDt': startDt,
    'endDt': endDt,
    'kdc':kdc,
    'pageNo': pageNo if pageNo != '' else '1',
    'pageSize': pageSize
    }


    # 1. 사용자로부터 원하는 API 종류를 입력받음
    print("사용 가능한 API 목록:", list(dt.url_dict.keys()))
    selected_api = input("호출할 API 이름을 입력하세요 (예: 인기대출도서 조회, 기본값: 정보공개): ")
    
    try:
        # 2. 변경된 함수 호출
        result_df = dt.read_xml_by_key(
            selected_api if selected_api != '' else '정보공개', 
            params
        )
        
        # 3. 결과 출력
        print("\n--- 변환된 데이터프레임 결과 ---")
        print(result_df.head())
        path = f'./datas/result_{sex}_{age}_{detail_region}_{startDt}_{endDt}.csv'
        result_df.to_csv(path, index=False)
        
    except Exception as e:
        print(f"\n데이터를 가져오는 중 오류가 발생했습니다: {e}")


    # 2. 추출된 데이터의 url에서 책 개요 추출
    try:
        #df = result_df
        
        # 테스트를 위해 상위 50개만 먼저 돌려보시는 것을 추천합니다.
        # 전체를 다 하려면 df 대신 df.head(50) 등으로 속도를 확인해 보세요.
        txtdf = dt.extractTxt_fast(result_df) 
        txt_path = f'./datas/txts_{sex}_{age}_{detail_region}_{startDt}_{endDt}.csv'
        
        txtdf.to_csv(txt_path, index=False, encoding='utf-8-sig')
    except FileNotFoundError:
        print(f"[!] {path} 파일이 해당 경로에 없습니다.")