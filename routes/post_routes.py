# routes/post_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session
from db import get_db
import pymysql
from werkzeug.utils import secure_filename
import os

bp = Blueprint('post', __name__, url_prefix='/post')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')  #파일 업로드 경로
# os.getcwd() : 현재 작업 디렉토리의 경로를 문자열로 반환
# os.path.join() : 이 경로에 추가 경로를 결합할 때 사용
# 현재 작업 디렉토리 경로만 필요하다면 `os.getcwd()`만 사용하면 된다.

# 글 작성
@bp.route('/<int:board_id>/write', methods=['GET', 'POST'])
def post_write(board_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()

    if request.method == 'GET':
        return render_template('post/write.html', board_id=board_id)

    title = request.form['title']
    content = request.form['content']
    file = request.files.get('file')    # 사용자가 업로드한 파일 브라우저로부터 수신
    filename = None     # 파일 이름 초기값은 None

    if file and file.filename:  # 파일과 파일 이름이 있으면 즉, 유저가 파일을 올렸으면
        filename = secure_filename(file.filename)   # 사용자가 서버의 파일시스템이 있는 파일을 수정하는 것을 방지하기 위해 사용
        file.save(os.path.join(UPLOAD_FOLDER, filename))    # 저장 경로 + 파일 이름해서 서버에 저장

    cursor.execute(
        'INSERT INTO question (title, content, create_date, user_id, board_id, filename) '
        'VALUES(%s, %s, NOW(), %s, %s, %s)',
        (title, content, user_id, board_id, filename)   # filename 포함해서 DB에 저장
    )   # 글과 연결된 첨부파일이 무엇인지 추적할 수 있음
    db.commit()
    return redirect(url_for('post.post_list', board_id=board_id))

# 글 목록
@bp.route('/list/<int:board_id>')
def post_list(board_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT * FROM board WHERE id = %s', (board_id))
    board = cursor.fetchone()

    keyword = request.args.get('q', '').strip()     # 검색 키워드
    filter_type = request.args.get('filter', 'all')     # 제목/내용/제목+내용

    if keyword:
        like = f"%{keyword}%"   # 검색 키워드 f-string화. 문자열 포매팅

        if filter_type == 'title':  # 제목 기준 검색
            sql = "SELECT * FROM question WHERE board_id = %s AND title LIKE %s ORDER BY create_date DESC"
            cursor.execute(sql, (board_id, like))
        elif filter_type == 'content':  # 내용 기준 검색
            sql = "SELECT * FROM question WHERE board_id = %s AND content LIKE %s ORDER BY create_date DESC"
            cursor.execute(sql, (board_id, like))
        else:   # 'all' 또는 그 외
            sql = "SELECT * FROM question WHERE board_id = %s AND (title LIKE %s OR content LIKE %s) ORDER BY create_date DESC"
            cursor.execute(sql, (board_id, like, like))
    else:
        cursor.execute("SELECT * FROM question WHERE board_id = %s ORDER BY create_date DESC", (board_id))

    posts = cursor.fetchall()   # DB에서 게시글 전부 가져오기
    return render_template('post/list.html', posts=posts, board=board)

# 글 상세 보기
@bp.route('/<int:board_id>/detail/<int:post_id>')
def post_detail(board_id, post_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT * FROM board WHERE id = %s', (board_id,))
    board = cursor.fetchone()

    cursor.execute('SELECT * FROM question WHERE id = %s AND board_id = %s', (post_id, board_id))
    post = cursor.fetchone()

    cursor.execute('SELECT * FROM answer WHERE question_id = %s ORDER BY create_date ASC', (post_id))
    answers = cursor.fetchall()

    return render_template('post/detail.html', post=post, board=board, answers=answers)

# 글 수정
@bp.route('/<int:board_id>/edit/<int:post_id>', methods=['GET', 'POST'])
def post_edit(board_id, post_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM question WHERE id = %s AND board_id = %s', (post_id, board_id))
    post = cursor.fetchone()

    if post is None or post['user_id'] != session['user_id']:
        return "권한이 없습니다.", 403

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files.get('file')    # 파일 수신
        filename = post['filename']  # 기본값: 기존 파일 유지

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))    # [파일 경로 + 이름]으로 저장

        cursor.execute(
            'UPDATE question SET title=%s, content=%s, filename=%s WHERE id=%s AND board_id=%s',
            (title, content, filename, post_id, board_id)   #filename 포함 DB에 저장
        )
        db.commit()
        return redirect(url_for('post.post_detail', board_id=board_id, post_id=post_id))

    return render_template('post/edit.html', post=post, board_id=board_id)

#글 삭제
@bp.route('/<int:board_id>/delete/<int:post_id>')
def post_delete(board_id, post_id):     #게시판 id, 글 id
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM question WHERE id = %s AND board_id = %s', (post_id, board_id))
    post = cursor.fetchone()    #게시글 SELECT문에서 한 줄 가져 옴

    if post is None or post['user_id'] != session['user_id']:   #글 작성자와 현재 사용자가 다르면
        return "권한이 없습니다.", 403

    cursor.execute('DELETE FROM question WHERE id = %s AND board_id = %s', (post_id, board_id))
    db.commit()
    return redirect(url_for('post.post_list', board_id=board_id))

#댓글 등록
@bp.route('/<int:board_id>/answer/<int:post_id>/write', methods=['POST'])
def answer_write(board_id, post_id):
    if 'user_id' not in session:    #로그인 여부 확인
        return redirect(url_for('auth.login'))

    content = request.form['content']
    user_id = session['user_id']

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO answer (content, create_date, user_id, question_id) VALUES (%s, NOW(), %s, %s)",
        (content, user_id, post_id)
    )   #answer테이블에 내용, 유저id, 글 id INSERT
    db.commit()
    return redirect(url_for('post.post_detail', board_id=board_id, post_id=post_id))

#댓글 수정
@bp.route('/<int:board_id>/answer/<int:answer_id>/edit', methods=['GET', 'POST'])
def answer_edit(board_id, answer_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM answer WHERE id = %s", (answer_id))
    answer = cursor.fetchone()

    if answer is None or answer['user_id'] != session['user_id']:
        return "권한이 없습니다.", 403

    if request.method == 'POST':
        content = request.form['content']
        cursor.execute("UPDATE answer SET content = %s WHERE id = %s", (content, answer_id))
        db.commit()
        return redirect(url_for('post.post_detail', board_id=board_id, post_id=answer['question_id']))  #answer 테이블의 id를 post_id에 대입
    
    return render_template('post/answer_edit.html', answer=answer, board_id=board_id)

#댓글 삭제
@bp.route('/<int:board_id>/answer/<int:answer_id>/delete')
def answer_delete(board_id, answer_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM answer WHERE id = %s", (answer_id))
    answer = cursor.fetchone()

    if answer is None or answer['user_id'] != session['user_id']:
        return "권한이 없습니다.", 403

    post_id = answer['question_id']
    cursor.execute("DELETE FROM answer WHERE id = %s", (answer_id))
    db.commit()
    return redirect(url_for('post.post_detail', board_id=board_id, post_id=post_id))