import pandas as pd
import xml.etree.ElementTree as ET
import requests

# 전역변수 데이터

data_path = r'C:\Users\USER\Desktop\develop\공모전\console_test\datacode_list.xlsx'
data_path = data_path.replace('\\', '/')

region = pd.read_excel(data_path, sheet_name='지역')
detail = pd.read_excel(data_path, sheet_name='세부주제')
genre = pd.read_excel(data_path, sheet_name='장르')
isbn = pd.read_excel(data_path, sheet_name='ISBN')
age = pd.read_excel(data_path, sheet_name='나이')
sex = pd.read_excel(data_path, sheet_name='성별')

master_data_dict = {
    "지역": region,
    "세부주제": detail,
    "장르": genre,
    "ISBN": isbn,
    "나이": age,
    "성별": sex
}


url_dict = {
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



# 동적 열 추상화 기반의 통합 검색 함수
def search_master_data(category, query):
    """
    작성하신 엑셀 로드 환경에서 시트별로 서로 다른 열 이름을 동적으로 파악하여, 
    '코드값'을 제외한 모든 텍스트 열을 대상으로 검색어(query)를 자동 탐색하는 통합 함수
    """
    # 카테고리(시트명) 유효성 검사
    if category not in master_data_dict:
        return f"❌ 존재하지 않는 시트(카테고리)입니다. 선택 가능: {list(master_data_dict.keys())}"
    
    # 해당 시트의 데이터프레임 카피 복사
    df = master_data_dict[category].copy()
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


# 변경된 read_xml 함수
def read_xml_by_key(api_key, params):
    """
    url_dict의 키(api_key)를 받아 해당 URL의 XML 데이터를 데이터프레임으로 반환하는 함수
    """
    # 1. 딕셔너리에서 키에 해당하는 URL 가져오기
    if api_key not in url_dict:
        raise KeyError(f"'{api_key}'은(는) 존재하지 않는 API 키 이름입니다. url_dict를 확인해주세요.")
    
    url = url_dict[api_key]
    print(f"[{api_key}] API 호출 중... (URL: {url})")

    # 2. API 호출 및 데이터 가져오기
    response = requests.get(url, params=params)
    response.raise_for_status()
    response.encoding = 'utf-8'
    
    xml_text = response.text
    root = ET.fromstring(xml_text)

    # 3. XML 파싱하여 리스트에 저장
    parsed_list = []
    # 도서관정보나루 API의 일반적인 데이터 구조인 <doc> 태그 탐색
    # (메뉴에 따라 태그 구성이 다를 경우 .findall('.//*') 등으로 유연하게 대처할 수도 있습니다)
    for doc in root.findall('.//doc'):
        doc_dict = {}
        for child in doc:
            doc_dict[child.tag] = child.text
        parsed_list.append(doc_dict)

    # 4. 데이터프레임 변환 및 반환
    df = pd.DataFrame(parsed_list)
    return df


# 3. 실제 통합 검색 사용 예시
if __name__ == "__main__":
    print("\n" + "="*50 + "\n[검색 알고리즘 테스트 실행]\n" + "="*50)
    
    sex = input('성별 입력(남성, 여성, 미상): ')
    age = input('나이대 입력(영유아(0~5세),\
                 유아(6~7세), 초등(8~13세), 청소년(14~19세),\
                 20대, ..., 60세 이상, 미상, \
                1, 2학년, 3, 4학년, 5, 6학년, 중등, 고등): ')
    #region = input('상위행정구역 이름(특별/광역시, 도): ')
    detail_region = input('세부지역명 입력(시, 군, 구): ')

    # api url 접근용 딕셔너리
    params = {
    'authKey': '',  # 도서관정보나루에서 발급받은 Key
    'startDt': '2026-05-01',
    'endDt': '2026-05-31',
    'pageNo': '1',
    'pageSize': '100'
    }

    print(search_master_data('성별', sex))
    print(search_master_data('나이', age))
    #print(search_master_data('지역', region))
    print(search_master_data('지역', detail_region))

    print(type(sex), type(age), type(detail_region))

# 1. 사용자로부터 원하는 API 종류를 입력받음
    print("사용 가능한 API 목록:", list(url_dict.keys()))
    selected_api = input("호출할 API 이름을 입력하세요 (예: 인기대출도서 조회): ")
    
    try:
        # 2. 변경된 함수 호출
        result_df = read_xml_by_key(selected_api, params)
        
        # 3. 결과 출력
        print("\n--- 변환된 데이터프레임 결과 ---")
        print(result_df.head())
        result_df.to_csv(f'data/result_{sex}_{age}_{detail_region}.csv', index=False)
        
    except Exception as e:
        print(f"\n데이터를 가져오는 중 오류가 발생했습니다: {e}")
