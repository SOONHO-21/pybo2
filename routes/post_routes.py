# routes/post_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session
from db import get_db
import pymysql
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
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

    is_secret = True if request.form.get('is_secret') else False
    secret_pw = request.form.get('secret_pw')

    secret_pw_hash = None
    if is_secret:
        if not secret_pw:
            flash("비밀글 비밀번호를 입력해야 합니다.")
            return redirect(url_for('post.post_write', board_id=board_id))
        secret_pw_hash = generate_password_hash(secret_pw)

    if file and file.filename:  # 파일과 파일 이름이 있으면 즉, 유저가 파일을 올렸으면
        filename = secure_filename(file.filename)   # 사용자가 서버의 파일시스템이 있는 파일을 수정하는 것을 방지하기 위해 사용
        file.save(os.path.join(UPLOAD_FOLDER, filename))    # 저장 경로 + 파일 이름해서 서버에 저장

    cursor.execute(
        'INSERT INTO question (title, content, create_date, user_id, board_id, filename, is_secret, secret_pw) '
        'VALUES(%s, %s, NOW(), %s, %s, %s, %s, %s)',
        (title, content, user_id, board_id, filename, is_secret, secret_pw_hash)   # filename 포함해서 DB에 저장
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
@bp.route('/<int:board_id>/detail/<int:post_id>', methods=['GET', 'POST'])
def post_detail(board_id, post_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM question WHERE id = %s AND board_id = %s', (post_id, board_id))
    post = cursor.fetchone()

    if not post:
        return "글을 찾을 수 없습니다.", 404

    cursor.execute('SELECT * FROM board WHERE id = %s', (board_id))
    board = cursor.fetchone()

    is_authorized = False

    if post['is_secret']:
        if request.method == 'POST':
            input_pw = request.form['input_pw']
            if not check_password_hash(post['secret_pw'], input_pw):
                flash("비밀번호가 일치하지 않습니다.")
                return redirect(url_for('post.post_detail', board_id=board_id, post_id=post_id))
            else:
                is_authorized = True
        else:
            post['content'] = None
    else:
        is_authorized = True

    return render_template('post/detail.html', post=post, board=board, board_id=board_id, is_authorized=is_authorized)

# 글 수정
@bp.route('/<int:board_id>/edit/<int:post_id>', methods=['GET', 'POST'])    #/게시판아이디/edit/게시글아이디
def post_edit(board_id, post_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM question WHERE id = %s AND board_id = %s', (post_id, board_id))
    post = cursor.fetchone()

    if post is None or post['user_id'] != session['user_id']:   #현재 세션 사용자와 글 올린 사용자 비교
        return "권한이 없습니다.", 403

    # 비밀글이면 먼저 비밀번호 확인
    if post['is_secret']:
        # 인증 여부 확인 (session에 저장)
        if f'post_edit_auth_{post_id}' not in session:  # 현재 이 글에 대해 인증된 적 있는지 확인
            #세션에 인증 플래그 없으면 -> 비밀번호 입력 폼을 먼저 보여줘야 함. 인증 세션의 이름 규칙은 여기서 정해진 것
            if request.method == 'POST' and 'input_pw' in request.form: # POST + input_pw 있으면 -> 비밀번호 검증
                input_pw = request.form['input_pw']     #사용자가 입력한 글 비밀번호
                if not check_password_hash(post['secret_pw'], input_pw):    # 글 비밀번호가 맞지 않으면(해시값 검증)
                    flash("비밀번호가 일치하지 않습니다.")  # flash 메시지 + 리다이렉트
                    return redirect(url_for('post.post_edit', board_id=board_id, post_id=post_id))
                else:   # 글 비밀번호가 맞으면
                    session[f'post_edit_auth_{post_id}'] = True # post_edit_auth_글ID 플래그 저장
                                                                # 여기서부터 이름 패턴이 프로그램에 저장되기 시작
                    return redirect(url_for('post.post_edit', board_id=board_id, post_id=post_id))  # 그러고 글 수정 템플릿으로 리다이렉트
            # 비밀번호 입력 폼 렌더링
            return render_template('post/check_pw.html', board_id=board_id, post_id=post_id)
        
    # 글 수정 폼
    if request.method == 'POST' and 'title' in request.form:
        title = request.form['title']
        content = request.form['content']
        file = request.files.get('file')
        filename = post['filename']

        is_secret = True if request.form.get('is_secret') else False    # 체크박스로 비밀 글 여부 결정
        secret_pw = request.form.get('secret_pw')   # 글 비밀번호 get
        secret_pw_hash = post['secret_pw']  # get한 글 비밀번호 해시

        if is_secret:   #비밀 글이라면
            if secret_pw:   #비밀번호를 입력했으면
                secret_pw_hash = generate_password_hash(secret_pw)  # 설정한 글 비밀번호 해시 저장
        else:   # 비밀 글이 아니라면
            secret_pw_hash = None

        if file and file.filename:  # 파일 여부 검증
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))    # 파일 경로 + 이름 DB 저장

        cursor.execute(
            'UPDATE question SET title=%s, content=%s, filename=%s, is_secret=%s, secret_pw=%s WHERE id=%s AND board_id=%s',
            (title, content, filename, is_secret, secret_pw_hash, post_id, board_id)
        )
        db.commit()
        session.pop(f'post_edit_auth_{post_id}', None)  # 글 수정 완료 후 인증 세션 플래그 제거
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