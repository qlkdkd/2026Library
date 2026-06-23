import xml.etree.ElementTree as ET
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
# config 모듈에서 전역 변수 참조
from config import MASTER_DATA_DICT, URL_DICT

def search_master_data(target_key, input_value):
    """사용자 입력값에 해당하는 오픈 API용 코드값을 반환합니다."""
    if target_key not in MASTER_DATA_DICT:
        return None
    
    target_df = MASTER_DATA_DICT[target_key]
    if target_df.empty:
        return None

    # 지역 코드 검색 예외 처리 (상위/세부 행정구역 조합)
    if target_key == '지역' and isinstance(input_value, tuple):
        prov, dist = input_value
        result = target_df[(target_df['광역시도명'] == prov) & (target_df['세부지역명'] == dist)]
        if not result.empty:
            return str(result.iloc[0]['코드값'])
    else:
        # 일반 코드북 매핑 (성별, 나이 등)
        result = target_df[target_df['상세'] == input_value]
        if not result.empty:
            return str(result.iloc[0]['코드값'])
            
    return None

def fetch_library_data(api_key_name, params):
    """url_dict의 키를 기반으로 API 데이터를 페이징 처리하여 데이터프레임으로 가져옵니다."""
    if api_key_name not in URL_DICT:
        raise KeyError(f"'{api_key_name}'은(는) 존재하지 않는 API 이름입니다.")
        
    url = URL_DICT[api_key_name]
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
        return pd.DataFrame()

def run_kmeans_clustering(df, n_clusters=5):
    """수집된 데이터프레임을 전처리하여 KMeans 군집화를 실행하고 시각화합니다."""
    print(f"\n[*] 데이터 전처리 및 KMeans 군집화 수행 중 (K={n_clusters})...")
    analysis_df = df.copy()
    
    numeric_cols = ['ranking', 'publication_year', 'loan_count']
    for col in numeric_cols:
        if col in analysis_df.columns:
            analysis_df[col] = pd.to_numeric(analysis_df[col], errors='coerce')
            
    cluster_features = analysis_df[numeric_cols].dropna()
    
    if len(cluster_features) < n_clusters:
        print("[!] 데이터 부족으로 군집화를 수행할 수 없습니다.")
        return df
        
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(cluster_features)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_features)
    
    analysis_df.loc[cluster_features.index, 'cluster'] = cluster_labels
    analysis_df['cluster'] = analysis_df['cluster'].fillna(-1).astype(int)
    
    # 그래프 시각화
    plt.rc('font', family='Malgun Gothic')
    plt.rc('axes', unicode_minus=False)
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 1. 발행년도 vs 대출건수
    sns.scatterplot(
        x='publication_year', y='loan_count', hue='cluster', 
        palette='tab10', data=analysis_df[analysis_df['cluster'] != -1], 
        alpha=0.7, ax=axes[0]
    )
    axes[0].set_title('발행년도 vs 대출건수 군집 분포')
    axes[0].grid(True, linestyle='--', alpha=0.5)
    
    # 2. PCA 차원 축소
    pca = PCA(n_components=2, random_state=42)
    pca_features = pca.fit_transform(scaled_features)
    pca_df = pd.DataFrame(pca_features, columns=['PCA1', 'PCA2'])
    pca_df['cluster'] = cluster_labels
    
    sns.scatterplot(
        x='PCA1', y='PCA2', hue='cluster', 
        palette='tab10', data=pca_df, alpha=0.7, ax=axes[1]
    )
    axes[1].set_title('PCA 2차원 축소 기반 군집 시각화')
    axes[1].grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()
    
    return analysis_df