from DataSearch import DataSearcher

dt = DataSearcher()

#1. 인기 데이터 추출
params = {
    'authKey' : dt.authKey,
    'startDt' : '2026-06-01',
    'endDt' : '2026-06-29',
    'gender' : dt.srchCode('성별', '남성'),
    'age' : dt.srchCode('나이', '20대'),
    'region' : dt.srchCode('지역', '경기도'),
    'dtl_region' : dt.srchCode('세부지역', '의정부시'),
    'pageSize' : 1000
}


print(dt.srchCode('성별', '남성'))
print(dt.srchCode('나이', '20대'))
print(dt.srchCode('지역', '경기도'))
print(dt.srchCode('세부지역', '의정부시'))

loanItemSrch_df = dt.read_xml_by_key('인기대출도서 조회', params)
loanItemSrch_df.to_csv('loanItemSrch_2026-06-01_2026-06-29_남성_20대_경기도_의정부시.csv', index=False)
