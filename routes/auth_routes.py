from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()

        error = None
        cursor.execute('SELECT id FROM user WHERE username = %s', (username,))
        if cursor.fetchone():
            error = '이미 존재하는 사용자입니다.'
            flash(error)

        if error is None:
            hashed_pw = generate_password_hash(password)
            cursor.execute('INSERT INTO user (username, password) VALUES (%s, %s)', (username, hashed_pw))
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM user WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user is None or not check_password_hash(user["password"], password):
            flash('사용자 이름 또는 비밀번호가 잘못되었습니다.')
        else:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']  # 이 줄을 추가
            return redirect(url_for('board.board_list'))

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))