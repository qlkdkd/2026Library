import pandas as pd
import requests
import xml.etree.ElementTree as ET


class DataSearcher:
    def __init__(self):

        # 코드 정보 데이터
        self.codeList = './resource/datacode_list.xlsx'
        
        self.region = pd.read_excel(self.codeList, sheet_name='지역')
        self.dtl_region = pd.read_excel(self.codeList, sheet_name='세부지역')
        self.dtl_kdc = pd.read_excel(self.codeList, sheet_name='세부주제')
        self.kdc = pd.read_excel(self.codeList, sheet_name='장르')
        self.addCode = pd.read_excel(self.codeList, sheet_name='ISBN')
        #self.addition_symbol = self.addCode
        self.age = pd.read_excel(self.codeList, sheet_name='나이')
        self.gender = pd.read_excel(self.codeList, sheet_name='성별')

        self.codeMasterData = {
            '지역' : self.region,
            '세부지역' : self.dtl_region,
            '대주제' : self.kdc,
            '세부주제' : self.dtl_kdc,
            'isbn 부가기호' : self.addCode,
            '나이' : self.age,
            '성별' : self.gender
        }


        # api별 url 딕셔너리
        self.url = 'http://data4library.kr/api/'
        self.url_dict = {
            '정보공개' : f'{self.url}libSrch',
            '도서관별 장서/대출 데이터 조회' : f'{self.url}itemSrch',
            '인기대출도서 조회' : f'{self.url}loanItemSrch',
            '마니아를 추천도서' : f'{self.url}recommandList',
            '다독자 추천도서' : f'{self.url}recommandList',
            '도서 상세 조회' : f'{self.url}srchDtlList',
            '도서 키워드 목록' : f'{self.url}keywordList',
            '도서별 이용 분석' : f'{self.url}usageAnalysisList',
            '도서관/지역별 인기대출 도서 조회' : f'{self.url}loanItemSrchByLib',
            '도서관별 대출반납추이' : f'{self.url}usageTrend',
            '도서관별 도서 소장여부 및 대출 가능여부 조회' : f'{self.url}/bookExist',
            '대출 급상승 도서' : f'{self.url}hotTrend',
            '도서 소장 도서관 조회' : f'{self.url}/libSrchByBook',
            '도서관별 통합정보' : f'{self.url}/libSrch',
            '도서관별 인기대출도서 통합' : f'{self.url}/loanItemSrchByLib',
            '도서 검색' : f'{self.url}/srchBooks',
            '이달의 키워드' : f'{self.url}monthlyKeywords',
            '지역별 독서량/독서율' : f'{self.url}readQt',
            '신착도서 조회' : f'{self.url}newArrivalBook'
        }

        # 인증키
        self.authKey = ''

        # 도서관 정보
        self.libDf = pd.read_csv('./resource/library_list.csv')

        # api별 태그 모음
        self.tag_mapping = {
            '정보공개': {'parent': 'libs', 'target': 'lib', 'paging': False},
            '도서관별 장서/대출 데이터 조회': {'parent': 'docs', 'target': 'doc', 'paging': True},
            '인기대출도서 조회': {'parent': 'docs', 'target': 'doc', 'paging': True},
            '마니아 추천도서': {'parent': 'books', 'target': 'book', 'paging': False},
            '다독자 추천도서': {'parent': 'books', 'target': 'book', 'paging': False},
            '도서 상세 조회': {'parent': 'docs', 'target': 'doc', 'paging': False},
            '도서 키워드 목록': {'parent': 'keywords', 'target': 'keyword', 'paging': False},
            '도서별 이용 분석': {'parent': 'coDocs', 'target': 'coDoc', 'paging': False},
            '도서관/지역별 인기대출 도서 조회': {'parent': 'docs', 'target': 'doc', 'paging': True},
            '도서관별 대출반납추이': {'parent': 'histories', 'target': 'history', 'paging': True},
            '도서관별 도서 소장여부 및 대출 가능여부 조회': {'parent': 'result', 'target': 'loanAvailable', 'paging': False},
            '대출 급상승 도서': {'parent': 'docs', 'target': 'doc', 'paging': False},
            '도서 소장 도서관 조회': {'parent': 'libs', 'target': 'lib', 'paging': True},
            '도서관별 통합정보': {'parent': 'libs', 'target': 'lib', 'paging': True},
            '도서관별 인기대출도서 통합': {'parent': 'docs', 'target': 'doc', 'paging': True},
            '도서 검색': {'parent': 'docs', 'target': 'doc', 'paging': True},
            '이달의 키워드': {'parent': 'keywords', 'target': 'keyword', 'paging': False},
            '지역별 독서량/독서율': {'parent': 'results', 'target': 'result', 'paging': False},
            '신착 도서 목록': {'parent': 'docs', 'target': 'doc', 'paging': True}
        }


    # 코드 마스터 데이터에서 특정 코드 검색
    def srchCode(self, category, query):
        if category not in self.codeMasterData:
           return f'존재하지 않는 시트(카테고리)입니다. 선택 가능: {list(self.codeMasterData.keys())}'
    
        df = self.codeMasterData[category].copy()
        query = str(query).strip()

        # 문자열 데이터가 담긴 열 이름 찾기
        searchable_columns = [col for col in df.columns if col != '코드값']

        if not searchable_columns:
            return '검색 가능한 데이터 열이 해당 시트에 존재하지 않습니다.'
        
        # 모든 대상 열의 데이터를 문자열로 변환한 뒤, 검색어 포함 여부 누적 계산
        condition = df[searchable_columns[0]].astype(str).str.contains(query, na=False)
        for col in searchable_columns[1:]:
            condition |= df[col].astype(str).str.contains(query, na=False)

        # 조건에 일치하는 결과 필터링
        matched_result = df[condition]

        if matched_result.empty:
            return f"'{query}'에 매핑되는 코드를 [{category}] 시트에서 찾을 수 없습니다."
        
        print(f'검색결과')
        return matched_result['코드값'].to_string(index=False)
    

    def read_xml_by_key(self, api_key_name, params):
            """
            api_key_name을 기반으로 parent_tag, target_tag, paging 설정을
            자동으로 인지하여 데이터를 수집하는 만능 메서드
            """
            if api_key_name not in self.url_dict:
                raise KeyError(f"'{api_key_name}'은(는) 존재하지 않는 API 이름입니다.")
                
            url = self.url_dict[api_key_name]
            
            # 💡 매핑 데이터에서 태그 및 페이징 정보 자동 추출
            config = self.tag_mapping[api_key_name]
            parent_tag = config['parent']
            target_tag = config['target']
            paging_required = config['paging']
            
            all_dfs = []
            
            # Case 1: 페이징이 필요 없는 단일 요청 API (예: 정보공개, 도서 상세 조회 등)
            if not paging_required:
                print(f"\n[*] [{api_key_name}] 단일 데이터 요청 시작 (자동 태그 세팅 -> <{parent_tag}>/<{target_tag}>)...")
                try:
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    response.encoding = 'utf-8'
                    
                    root = ET.fromstring(response.text)
                    parsed_list = []
                    for row_data in root.findall(f'.//{parent_tag}/{target_tag}'):
                        row_dict = {child.tag: child.text for child in row_data}
                        parsed_list.append(row_dict)
                        
                    if parsed_list:
                        final_df = pd.DataFrame(parsed_list)
                        print(f"[+] [{api_key_name}] 총 {len(final_df)}행 수집 및 변환 완료!")
                        return final_df
                except Exception as e:
                    print(f"[!] 데이터 수집 중 오류 발생: {e}")
                return pd.DataFrame()

            # Case 2: 페이징 처리가 필요한 대량 데이터 API (예: 인기대출도서 조회, 도서관별 통합정보 등)
            target_size = int(params.get('pageSize', 200))
            current_page = 1
            collected_rows = 0
            
            print(f"\n[*] [{api_key_name}] 페이징 데이터 연속 수집 시작 (목표: {target_size}건, 자동 태그 세팅 -> <{parent_tag}>)...")

            while collected_rows < target_size:
                req_size = min(1000, target_size - collected_rows)
                req_params = params.copy()
                req_params['pageNo'] = str(current_page)
                req_params['pageSize'] = str(req_size)
                
                try:
                    response = requests.get(url, params=req_params)
                    response.raise_for_status()
                    response.encoding = 'utf-8'
                    
                    root = ET.fromstring(response.text)
                    parsed_list = []
                    for row_data in root.findall(f'.//{parent_tag}/{target_tag}'):
                        row_dict = {child.tag: child.text for child in row_data}
                        parsed_list.append(row_dict)
                        
                    if not parsed_list:
                        break
                        
                    page_df = pd.DataFrame(parsed_list)
                    all_dfs.append(page_df)
                    
                    collected_rows += len(page_df)
                    print(f" -> {current_page}페이지 완료 ({len(page_df)}행, 누적: {collected_rows}/{target_size})")
                    
                    if len(page_df) < req_size:
                        break
                    current_page += 1
                    
                except Exception as e:
                    print(f"[!] 데이터 수집 중 오류 발생: {e}")
                    break

            if all_dfs:
                final_df = pd.concat(all_dfs, ignore_index=True)
                print(f"[+] [{api_key_name}] 총 {len(final_df)}행 통합 데이터프레임 변환 완료!")
                return final_df
            else:
                print("[!] 수집된 데이터가 없습니다.")
                return pd.DataFrame()
            

    def findLibrary(self, libName):
        return int(self.libDf.loc[self.libDf.values == libName, '도서관코드'])



# 테스트
if __name__ == '__main__':
    ds = DataSearcher()
    test = ds.srchCode('세부지역', '의정부시')
    print('마스터데이터에서 코드 찾기 테스트 결과:', test)

    #print('\napi 태그 매핑 리스트')
    #print(ds.tag_mapping.head())

    params = {
        'authKey':ds.authKey,
        'libCode':ds.findLibrary('의정부과학도서관')
    }

    test1 = ds.read_xml_by_key('정보공개', params)
    print('xml 데이터프레임 변환 테스트:')
    print(test1.head())
    test1.to_csv(f'./extracted_data/apiTest.csv', index=False)
