import requests
import pandas as pd

class GetNearestLib:
    def __init__(self):
        self.libDf = pd.read_csv('./resource/library_list.csv')
        self.client_id = "1e3qhye3kh"
        self.client_secret = "F2i0z62kuMTxutTFaS6CluUw04gJdTRyalMpiGLK"
        self.url = url = "https://maps.apigw.ntruss.com/map-direction/v1/driving"

    # 네이버 지도 api를 활용해서 거리와 걸리는 시간 추출하기
    def getRoute(self, start_lng, start_lat, goal_lng, goal_lat):
        headers = {
            "X-NCP-APIGW-API-KEY-ID": self.client_id,
            "X-NCP-APIGW-API-KEY": self.client_secret
        }
        params = {
            "start": f"{start_lng},{start_lat}",
            "goal": f"{goal_lng},{goal_lat}",
            "option": "traoptimal" 
        }

        response = requests.get(self.url, headers=headers, params=params)

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
    
    def findNearestLib(self, dtl_region, start_lng, start_lat):
        cond = self.libDf['주소'].str.contains(dtl_region) == True
        regionLibDf = self.libDf[cond]

        goal_lng = regionLibDf['경도']
        goal_lat = regionLibDf['위도']
        goal_name = regionLibDf['도서관명']

        lib_list = []

        for lng, lat, name in zip(goal_lng, goal_lat, goal_name):
            dist, duration = self.getRoute(start_lng, start_lat, lng, lat)
            print(f'{name}까지 이동거리: {dist:.2f}km, 소요시간: {duration:.2f}분')
            lib_list.append([name, dist, duration])

        return  sorted(lib_list, key=lambda x: x[1])[0]
    

if __name__ == '__main__':
    gnl = GetNearestLib()
    dtl_region = '남양주시'
    nearest_lib = gnl.findNearestLib(dtl_region, 127.0930, 37.7432)
    print(nearest_lib)