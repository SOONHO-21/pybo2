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
