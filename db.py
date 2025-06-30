# db.py
import pymysql
from flask import g
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로딩

def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(
            host='localhost',
            user='root',
            password=os.getenv('DB_PASSWORD'),  # .env 파일에서 비밀번호 로딩
            db='pybo',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor  # SELECT 결과를 튜플이 아닌 딕셔너리(컬럼명 기반)로 받기 위한 설정
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()