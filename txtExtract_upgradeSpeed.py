import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
from concurrent.futures import ThreadPoolExecutor  # 병렬 처리를 위한 라이브러리

# 책 1권의 URL에서 초록(개요)을 추출하는 단일 기능 함수
def fetch_single_abstract(url):
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

def extractTxt_fast(df):
    urls = df['bookDtlUrl'].tolist()
    names = df['bookname'].tolist()
    
    print(f"[*] 총 {len(urls)}건의 도서 개요 추출 시작 (병렬 처리)...")
    
    # ThreadPoolExecutor를 사용해 동시에 최대 10개의 요청을 보냅니다.
    # 서버에 무리가 가지 않는 선(10~20)에서 숫자를 조절하면 좋습니다.
    with ThreadPoolExecutor(max_workers=10) as executor:
        # executor.map은 순서를 보장하며 함수를 병렬로 실행해 줍니다.
        txt_list = list(executor.map(fetch_single_abstract, urls))
        
    print("[+] 모든 도서 개요 추출 완료!")
    
    txt_df = pd.DataFrame({
        'bookname': names,
        'info': txt_list
    })
    
    return txt_df

# 테스트
if __name__ == '__main__':
    # 기존에 저장된 결과 파일을 불러와 테스트
    try:
        df = pd.read_csv('result_남성_20대_의정부시.csv')
        
        # 테스트를 위해 상위 50개만 먼저 돌려보시는 것을 추천합니다.
        # 전체를 다 하려면 df 대신 df.head(50) 등으로 속도를 확인해 보세요.
        txtdf = extractTxt_fast(df.head(50)) 
        
        txtdf.to_csv('./datas/txtdf_fast.csv', index=False, encoding='utf-8-sig')
    except FileNotFoundError:
        print("[!] result_남성_20대_의정부시.csv 파일이 해당 경로에 없습니다.")