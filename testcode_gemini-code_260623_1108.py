import xml.etree.ElementTree as ET
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# 1. API 주소 사전 정의
url_dict = {
    '인기대출도서 조회': 'https://data4library.kr/api/loanItemSrch'
}

# 2. API 데이터 추출 함수 (페이징을 처리하여 안정적으로 500개 이상 수집)
def fetch_library_data(api_key_name, params):
    if api_key_name not in url_dict:
        raise KeyError(f"'{api_key_name}'은(는) 존재하지 않는 API 이름입니다.")
        
    url = url_dict[api_key_name]
    target_size = int(params.get('pageSize', 200))
    
    all_dfs = []
    current_page = 1
    collected_rows = 0
    
    print(f"\n[*] [{api_key_name}] 데이터 수집 시작 (목표 행 개수: {target_size})...")

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
            
            for doc in root.findall('.//doc'):
                doc_dict = {}
                for child in doc:
                    doc_dict[child.tag] = child.text
                parsed_list.append(doc_dict)
                
            if not parsed_list:
                break
                
            page_df = pd.DataFrame(parsed_list)
            all_dfs.append(page_df)
            
            collected_rows += len(page_df)
            if len(page_df) < req_size:
                break
            current_page += 1
            
        except Exception as e:
            print(f"[!] 데이터 수집 중 에러 발생: {e}")
            break

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        print(f"[+] 성공적으로 {len(final_df)}행의 데이터를 수집했습니다.")
        return final_df
    else:
        print("[!] 수집된 데이터가 없습니다.")
        return pd.DataFrame()

# 3. 비지도학습 군집화 및 시각화 함수
def run_kmeans_clustering(df, n_clusters=5):
    print(f"\n[*] 데이터 전처리 및 KMeans 군집화 수행 중 (K={n_clusters})...")
    
    # 분석용 복사본 생성
    analysis_df = df.copy()
    
    # 수치형 컬럼 변환 및 결측치 처리
    numeric_cols = ['ranking', 'publication_year', 'loan_count']
    for col in numeric_cols:
        if col in analysis_df.columns:
            analysis_df[col] = pd.to_numeric(analysis_df[col], errors='coerce')
            
    # 군집화에 사용할 수치 데이터만 드롭나(Dropna) 처리
    cluster_features = analysis_df[numeric_cols].dropna()
    
    if len(cluster_features) < n_clusters:
        print("[!] 데이터 행의 개수가 군집 수보다 적어 군집화를 수행할 수 없습니다.")
        return df
        
    # 데이터 스케일링 (KMeans 전 필수 단계)
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(cluster_features)
    
    # KMeans 모델 학습
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_features)
    
    # 원본 인덱스에 맞춰 군집 결과 매핑
    analysis_df.loc[cluster_features.index, 'cluster'] = cluster_labels
    analysis_df['cluster'] = analysis_df['cluster'].fillna(-1).astype(int)
    
    # --- 시각화 부분 ---
    plt.rc('font', family='Malgun Gothic') # Windows 한글 깨짐 방지
    plt.rc('axes', unicode_minus=False)
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 시각화 1: 발행년도 vs 대출건수 산점도
    sns.scatterplot(
        x='publication_year', y='loan_count', hue='cluster', 
        palette='tab10', data=analysis_df[analysis_df['cluster'] != -1], 
        alpha=0.7, ax=axes[0]
    )
    axes[0].set_title('발행년도 vs 대출건수 군집 분포')
    axes[0].set_xlabel('발행년도')
    axes[0].set_ylabel('대출건수')
    axes[0].grid(True, linestyle='--', alpha=0.5)
    
    # 시각화 2: PCA 차원 축소 산점도
    pca = PCA(n_components=2, random_state=42)
    pca_features = pca.fit_transform(scaled_features)
    pca_df = pd.DataFrame(pca_features, columns=['PCA1', 'PCA2'])
    pca_df['cluster'] = cluster_labels
    
    sns.scatterplot(
        x='PCA1', y='PCA2', hue='cluster', 
        palette='tab10', data=pca_df, alpha=0.7, ax=axes[1]
    )
    axes[1].set_title('PCA 2차원 축소 기반 군집 시각화')
    axes[1].set_xlabel('주성분 1 (PCA1)')
    axes[1].set_ylabel('주성분 2 (PCA2)')
    axes[1].grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()
    
    return analysis_df

# 4. 메인 실행 프로세스
if __name__ == "__main__":
    # 고정된 테스트용 API 파라미터 구성 (사용자 입력을 받으려면 input()으로 대체 가능)
    # 코드북 파라미터 세팅 (예시: 남성, 20대 등의 키값을 가이드 주신 코드로 매핑하여 사용 가능)
    api_params = {
        'authKey': '', # 발급받으신 Key
        'startDt': '2026-01-01',
        'endDt': '2026-06-01',
        'pageNo': '1',
        'pageSize': '500' # 분석 효율성을 위해 500개 수집
    }
    
    # Step 1: 데이터 로드
    raw_df = fetch_library_data('인기대출도서 조회', api_params)
    
    # Step 2: 군집화 및 시각화 진행
    if not raw_df.empty:
        # 5개의 군집(Cluster)으로 도서 분류 수행
        final_result_df = run_kmeans_clustering(raw_df, n_clusters=5)
        
        # 군집별 도서 개수 통계 출력
        print("\n[+] 군집별 데이터 개수 요약:")
        print(final_result_df['cluster'].value_counts().sort_index())
        
        # 결과 샘플 확인
        print("\n[+] 군집화 완료 데이터 샘플 (상위 5개):")
        print(final_result_df[['bookname', 'authors', 'loan_count', 'cluster']].head())