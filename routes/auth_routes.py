from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import smtplib
from email.mime.text import MIMEText

bp = Blueprint('auth', __name__, url_prefix='/auth')

#회원가입
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        realname = request.form['realname']
        company = request.form.get('company') or '무직'
        email = request.form.get('email') or None

        db = get_db()
        cursor = db.cursor()

        error = None
        cursor.execute('SELECT id FROM user WHERE username = %s', (username,))
        if cursor.fetchone():
            error = '이미 존재하는 사용자입니다.'

        if error is None:
            hashed_pw = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO user (username, password, realname, company, email) VALUES (%s, %s, %s, %s, %s)',
                (username, hashed_pw, realname, company, email)
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')

#로그인
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM user WHERE username = %s', (username))
        user = cursor.fetchone()

        if user is None or not check_password_hash(user["password"], password):
            flash('사용자 이름 또는 비밀번호가 잘못되었습니다.')
        else:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']  # 로그인한 사용자의 ID와 관리자 여부(True 또는 False)를 세션에서 꺼내기
            return redirect(url_for('board.board_list'))

    return render_template('auth/login.html')

#로그아웃
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

#프로필 보기
@bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT username, realname, company, email FROM user WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()

    return render_template('auth/profile.html', user=user)

#프로필 수정
@bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        realname = request.form['realname']
        company = request.form.get('company') or '무직'
        email = request.form.get('email') or None

        # 이메일 유효성 검사 (추가)
        import re
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if email and not re.match(email_pattern, email):
            flash("올바른 이메일 형식이 아닙니다.")
            return redirect(url_for('auth.edit_profile'))

        cursor.execute(
            'UPDATE user SET realname = %s, company = %s, email = %s WHERE id = %s',
            (realname, company, email, session['user_id'])
        )
        db.commit()
        return redirect(url_for('auth.profile'))

    cursor.execute('SELECT realname, company FROM user WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()
    return render_template('auth/edit_profile.html', user=user)

#아이디 찾기
@bp.route('/find_id', methods=['GET', 'POST'])
def find_id():
    if request.method == 'POST':
        realname = request.form['realname']
        company = request.form['company']

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'SELECT username FROM user WHERE realname = %s AND company = %s',
            (realname, company)
        )
        user = cursor.fetchone()

        if user:
            flash(f"아이디는 '{user['username']}' 입니다.")
        else:
            flash("일치하는 사용자가 없습니다.")

    return render_template('auth/find_id.html')

#비밀번호 찾기
@bp.route('/find_pw', methods=['GET', 'POST'])
def find_pw():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']

        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM user WHERE username = %s AND email = %s', (username, email))
        user = cursor.fetchone()

        if user:
            # 임시 비밀번호 생성
            temp_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            hashed_pw = generate_password_hash(temp_pw)

            # DB에 업데이트
            cursor.execute('UPDATE user SET password = %s WHERE id = %s', (hashed_pw, user['id']))
            db.commit()

            # 이메일 전송
            msg = MIMEText(f"임시 비밀번호: {temp_pw}\n로그인 후 반드시 비밀번호를 변경해주세요.")
            msg['Subject'] = "임시 비밀번호 발급 안내"
            msg['From'] = "wjdtnsgh386@gmail.com"    # 본인 Gmail 주소
            msg['To'] = email

            s = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            s.login("wjdtnsgh386@gmail.com", "tasg sgfi feth pqfa")  # 앱 비밀번호 사용
            s.send_message(msg)
            s.quit()

            flash("임시 비밀번호가 이메일로 전송되었습니다. 로그인 후 꼭 변경하세요!")
        else:
            flash("일치하는 회원 정보가 없습니다.")

    return render_template('auth/find_pw.html')