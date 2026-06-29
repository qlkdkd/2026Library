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
cond = libDf['주소'].str.contains('의정부시') == True
libDf = libDf[cond]
print(libDf)

goal_lng = libDf['경도']
goal_lat = libDf['위도']
goal_name = libDf['도서관명']
#print(goal_lng,'\n', goal_lat)

# 도서관별 거리, 걸리는 시간을 담은 리스트
lib_list = []
for lng, lat, name in zip(goal_lng, goal_lat, goal_name):
    dist, duration = get_naver_route(127.0930, 37.7432, lng, lat)
    print(f'{name}까지 이동거리: {dist:.2f}km, 소요시간: {duration:.2f}분')
    lib_list.append([name, dist, duration])

# 가장 가까운 거리의 도서관을 찾기 위해 정렬
sorted_libraries = sorted(lib_list, key=lambda x: x[1])

print(sorted_libraries)
