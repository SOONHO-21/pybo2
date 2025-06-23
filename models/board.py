from db import get_db

# 게시판 전체 조회
def get_all_boards():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM board ORDER BY id DESC')
    return cursor.fetchall()

# 특정 ID의 게시판 조회
def get_board_by_id(board_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM board WHERE id = %s', (board_id,))
    return cursor.fetchone()

# 게시판 이름으로 조회 (중복 방지용)
def get_board_by_name(name):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM board WHERE name = %s', (name,))
    return cursor.fetchone()

# 게시판 생성
def create_board(name):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO board (name) VALUES (%s)', (name,))
    db.commit()

# 게시판 수정
def update_board(board_id, name):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE board SET name = %s WHERE id = %s', (name, board_id))
    db.commit()

# 게시판 삭제
def delete_board(board_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM board WHERE id = %s', (board_id,))
    db.commit()