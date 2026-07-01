'''
- 자주 참조하는 파일들을 데이터베이스로 변환하기 위한 코드
'''



import os
import pandas as pd
from sqlalchemy import create_engine

# 1. MySQL 연결 설정
DB_USER = "root"
DB_PASSWORD = "sdh!1025"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "library_db"

connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(connection_string)

print("MySQL 데이터베이스 마이그레이션 시작...\n")

# ==========================================
# 파트 1: datacode_list.xlsx 내부 시트들 저장
# ==========================================
excel_file = "./resource/datacode_list.xlsx"

# 엑셀 시트 이름과 MySQL 테이블 이름 매핑
excel_sheets_to_db = {
    "지역": "region",
    "세부지역": "detail_region",
    "장르": "genre",
    "세부주제": "detail_subject",
    "ISBN": "isbn_code",
    "나이": "age_group",
    "성별": "gender"
}

if os.path.exists(excel_file):
    for sheet_name, table_name in excel_sheets_to_db.items():
        try:
            # 엑셀 파일에서 'sheet_name'에 해당하는 시트만 읽어옴
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # 컬럼명 공백 제거
            df.columns = df.columns.str.strip()
            
            # MySQL에 저장
            df.to_sql(table_name, con=engine, if_exists="replace", index=False)
            print(f"✅ 엑셀 시트 '{sheet_name}' -> MySQL '{table_name}' 테이블 저장 완료 ({len(df)}행)")
        except Exception as e:
            print(f"❌ 엑셀 시트 '{sheet_name}' 처리 중 오류 발생: {e}")
else:
    print(f"❌ 원본 엑셀 파일을 찾을 수 없습니다: {excel_file}")


# ==========================================
# 파트 2: 기존 library_list.csv 파일 저장
# ==========================================
csv_file = "./resource/library_list.csv"

if os.path.exists(csv_file):
    try:
        df_csv = pd.read_csv(csv_file, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df_csv = pd.read_csv(csv_file, encoding="cp949")
        
    df_csv.columns = df_csv.columns.str.strip()
    df_csv.to_sql("library", con=engine, if_exists="replace", index=False, chunksize=1000)
    print(f"✅ CSV 파일 '{csv_file}' -> MySQL 'library' 테이블 저장 완료 ({len(df_csv)}행)")
else:
    print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_file}")

print("\n모든 마이그레이션 작업이 완료되었습니다!")