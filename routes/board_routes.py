from flask import Blueprint, render_template, request, redirect, url_for, session
from db import get_db
import pymysql

bp = Blueprint('board', __name__, url_prefix='/board')

#게시판 목록
@bp.route('/')
def board_list():
    """
    게시판 목록 페이지를 보여주는 함수.
    모든 게시판을 최신순으로 불러와서 list.html 템플릿에 전달함.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM board ORDER BY id DESC')
    boards = cursor.fetchall()
    return render_template('board/list.html', boards=boards)


# 게시판 생성
@bp.route('/create', methods=['GET', 'POST'])
def board_create():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    if not session.get('is_admin', False):   # 현재 세션에 관리자인지 체크
        return "접근 권한이 없습니다.", 403

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO board (name, description, create_date) VALUES (%s, %s, NOW())', (name, description)
        )
        db.commit()
        return redirect(url_for('board.board_list'))

    return render_template('board/create.html')


# 게시판 수정
@bp.route('/<int:board_id>/edit', methods=['GET', 'POST'])
def board_edit(board_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    if not session.get('is_admin', False):   # 관리자 체크
        return "접근 권한이 없습니다.", 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM board WHERE id = %s', (board_id))
    board = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        cursor.execute(
            'UPDATE board SET name = %s, description = %s WHERE id = %s', (name, description, board_id)
        )
        db.commit()
        return redirect(url_for('board.board_list'))

    return render_template('board/edit.html', board=board)

# 게시판 삭제
@bp.route('/<int:board_id>/delete')
def board_delete(board_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    if not session.get('is_admin', False):   # 관리자 체크
        return "접근 권한이 없습니다.", 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM board WHERE id = %s', (board_id))
    db.commit()
    return redirect(url_for('board.board_list'))