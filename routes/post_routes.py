# routes/post_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session
from db import get_db

bp = Blueprint('post', __name__, url_prefix='/post')

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

    # POST 요청 처리
    title = request.form['title']
    content = request.form['content']

    cursor.execute(
        'INSERT INTO question (title, content, create_date, user_id, board_id) '
        'VALUES (%s, %s, NOW(), %s, %s)',
        (title, content, user_id, board_id)
    )
    db.commit()
    return redirect(url_for('post.post_list', board_id=board_id))

@bp.route('/list/<int:board_id>')
def post_list(board_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT * FROM board WHERE id = %s', (board_id,))
    board = cursor.fetchone()

    cursor.execute('SELECT * FROM question WHERE board_id = %s ORDER BY create_date DESC', (board_id,))
    posts = cursor.fetchall()

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

    if post is None:
        return redirect(url_for('post.post_list', board_id=board_id))

    return render_template('post/detail.html', post=post, board=board)

@bp.route('/<int:board_id>/edit/<int:post_id>', methods=['GET', 'POST'])
def post_edit(board_id, post_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT * FROM question WHERE id = %s AND board_id = %s', (post_id, board_id))
    post = cursor.fetchone()

    if post is None or post['user_id'] != session['user_id']:
        return "권한이 없습니다.", 403

    if request.method == 'GET':
        return render_template('post/edit.html', post=post, board_id=board_id)

    # POST 요청일 경우
    title = request.form['title']
    content = request.form['content']

    cursor.execute('UPDATE question SET title=%s, content=%s WHERE id=%s AND board_id=%s',
                   (title, content, post_id, board_id))
    db.commit()
    return redirect(url_for('post.post_detail', board_id=board_id, post_id=post_id))

@bp.route('/<int:board_id>/delete/<int:post_id>')
def post_delete(board_id, post_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT * FROM question WHERE id = %s AND board_id = %s', (post_id, board_id))
    post = cursor.fetchone()

    if post is None or post['user_id'] != session['user_id']:
        return "권한이 없습니다.", 403

    cursor.execute('DELETE FROM question WHERE id = %s AND board_id = %s', (post_id, board_id))
    db.commit()
    return redirect(url_for('post.post_list', board_id=board_id))