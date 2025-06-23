# init_db.py
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로딩

def init_database():
    with open('schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    conn = pymysql.connect(
        host='localhost',
        user='root',
        password=os.getenv('DB_PASSWORD'),  # .env에서 비밀번호 로딩
        db='pybo',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

    try:
        with conn.cursor() as cursor:
            for statement in schema_sql.split(';'):
                if statement.strip():
                    cursor.execute(statement)
        print("✅ 데이터베이스 초기화 완료")
    finally:
        conn.close()

if __name__ == '__main__':
    init_database()