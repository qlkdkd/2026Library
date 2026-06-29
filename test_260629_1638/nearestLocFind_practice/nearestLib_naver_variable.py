import requests
#import json
import pandas as pd

def get_naver_route(start_lng, start_lat, goal_lng, goal_lat):
    # 네이버 클라우드 플랫폼에서 발급받은 클라이언트 ID와 시크릿
    client_id = "1e3qhye3kh"
    client_secret = "F2i0z62kuMTxutTFaS6CluUw04gJdTRyalMpiGLK"
    
    url = "https://maps.apigw.ntruss.com/map-direction/v1/driving"
    # 파라미터 설정 (경도,위도 순서로 콤마로 연결)
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret
    }
    params = {
        "start": f"{start_lng},{start_lat}",
        "goal": f"{goal_lng},{goal_lat}",
        "option": "traoptimal" # 실시간 최적 경로
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data['code'] == 0:
            # 첫 번째 추천 경로의 거리(m)와 시간(ms) 추출
            route = data['route']['traoptimal'][0]
            distance_meter = route['summary']['distance'] # 미터 단위
            duration_ms = route['summary']['duration']     # 밀리초 단위
            
            distance_km = distance_meter / 1000
            duration_min = duration_ms / 1000 / 60
            
            return distance_km, duration_min
    return None, None

# 사용 예시 (내 위치 -> 1차 필터링된 도서관 위치)
# 예: 의정부역 -> 의정부과학도서관
libDf = pd.read_csv('./resource/library_list.csv')
cond = libDf['도서관명'] == '의정부미술도서관'
libDf = libDf[cond]
print(libDf)

goal_lng = libDf['경도'].iloc[0]
goal_lat = libDf['위도'].iloc[0]
print(goal_lng, goal_lat)

dist, duration = get_naver_route(127.0930, 37.7432, goal_lng, goal_lat)
print(f"실제 도로 이동 거리: {dist}km, 소요 시간: {duration}분")