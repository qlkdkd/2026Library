import pandas as pd
from utils import search_master_data, fetch_library_data, run_kmeans_clustering

def main():
    print("\n" + "="*50 + "\n[도서 추천 및 군집화 프로그램 테스트 실행]\n" + "="*50)
    
    # 1. 사용자로부터 파라미터 입력 받기
    input_sex = input('성별 입력(남성, 여성, 미상): ')
    input_age = input('나이대 입력(영유아(0~5세),\
                 유아(6~7세), 초등(8~13세), 청소년(14~19세),\
                 20대, ..., 60세 이상, 미상, \
                1, 2학년, 3, 4학년, 5, 6학년, 중등, 고등): ')
    prov_region = input('상위행정구역 이름(특별/광역시, 도): ')
    detail_region = input('세부지역명 입력(시, 군, 구): ')
    
    start_dt = input('검색시작일자 입력(yyyy-mm-dd): ')
    end_dt = input('검색종료일자 입력(yyyy-mm-dd): ')
    kdc_code = input('대주제 입력(KDC 대분류 코드): ')
    page_size = input('페이지 사이즈 입력(수집할 행 개수, 기본값: 200): ')
    pageNo = input('페이지 번호 입력(기본값: 1): ')
    page_size = page_size if page_size != '' else '200'

    # 2. 코드북 데이터 매핑을 통해 API 코드 변환
    sex_code = search_master_data('성별', input_sex)
    age_code = search_master_data('나이', input_age)
    region_code = search_master_data('지역', (prov_region, detail_region))

    # 3. API 요청용 파라미터 사전 구성
    api_params = {
        'authKey': 'af2db8effb80ec1510ae55194a4ee4a8eff2018a0fbe806e9c475d80e27e2f18', # 발급받으신 Key
        'startDt': start_dt,
        'endDt': end_dt,
        'kdc': kdc_code,
        'pageNo': pageNo if pageNo != '' else '1',
        'pageSize': page_size
    }
    
    # 유효한 코드값이 매핑되었다면 파라미터에 추가
    if sex_code: api_params['gender'] = sex_code
    if age_code: api_params['age'] = age_code
    if region_code: api_params['region'] = region_code

    # 4. 데이터 수집 진행
    raw_df = fetch_library_data('인기대출도서 조회', api_params)
    raw_df.to_csv('raw_df.csv', index=False)#, encoding='uft-8-sig')
    
    # 5. 비지도학습(군집화) 및 시각화 진행
    if not raw_df.empty:
        final_result_df = run_kmeans_clustering(raw_df, n_clusters=5)
        
        print("\n[+] 군집별 데이터 개수 요약:")
        print(final_result_df['cluster'].value_counts().sort_index())
        
        print("\n[+] 군집화 완료 데이터 샘플 (상위 5개):")
        print(final_result_df[['bookname', 'authors', 'loan_count', 'cluster']].head())
        
        # 분석 결과를 csv 파일로 임시 저장
        path = r'C:\Users\USER\Desktop\develop\공모전\console_test\testcode_260623_1139\datas'
        path = path.replace('\\', '/')

        output_filename = f"{path}/result_{input_sex}_{input_age}_{detail_region}.csv"
        
        final_result_df.to_csv(output_filename, index=False)#, encoding='utf-8-sig')
        print(f"\n[+] 분석 결과가 '{output_filename}' 파일로 저장되었습니다.")

if __name__ == "__main__":
    main()