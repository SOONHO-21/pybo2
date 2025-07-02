# routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
import re

bp = Blueprint('auth', __name__, url_prefix='/auth')

#회원가입
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        realname = request.form['realname']
        company = request.form.get('company') or '무직'
        email = request.form['email']

        if not email:
            flash("이메일은 필수 입력 항목입니다.")
            return redirect(url_for('auth.edit_profile'))

        # 이미 작성하신 정규표현식 검사도 이어서 가능
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            flash("올바른 이메일 형식이 아닙니다.")
            return redirect(url_for('auth.edit_profile'))

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
            return redirect(url_for('index'))

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
    cursor.execute('SELECT username, realname, company, email, profile_image FROM user WHERE id = %s', (session['user_id']))
    user = cursor.fetchone()

    return render_template('auth/profile.html', user=user)

PROFILE_FOLDER = os.path.join(os.getcwd(), 'static', 'profile')

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

        if not email:
            flash("이메일은 필수 입력 항목입니다.")
            return redirect(url_for('auth.edit_profile'))

        # 이메일 유효성 검사
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if email and not re.match(email_pattern, email):
            flash("올바른 이메일 형식이 아닙니다.")
            return redirect(url_for('auth.edit_profile'))

        # 파일 처리
        file = request.files.get('profile_image')
        filename = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(PROFILE_FOLDER, filename))   # PROFILE_FOLDER = static/profile

            #DB 업데이트
            cursor.execute(
                'UPDATE user SET realname = %s, company = %s, email = %s, profile_image = %s WHERE id = %s',
                (realname, company, email, filename, session['user_id'])
            )
        else:
            # 사용자가 "기본 이미지로 되돌리기" 버튼 누를 경우 (예: checkbox)
            if request.form.get('remove_image'):
                cursor.execute(
                    'UPDATE user SET realname = %s, company = %s, email = %s, profile_image = NULL WHERE id = %s',
                    (realname, company, email, session['user_id'])
                )
            else:
                cursor.execute(
                    'UPDATE user SET realname = %s, company = %s, email = %s WHERE id = %s',
                    (realname, company, email, session['user_id'])
                )
        db.commit()
        return redirect(url_for('auth.profile'))

    cursor.execute('SELECT realname, company, email, profile_image FROM user WHERE id = %s', (session['user_id']))
    user = cursor.fetchone()
    return render_template('auth/edit_profile.html', user=user)

#다른 사용자 프로필
@bp.route('/user/<int:user_id>')
def user_profile(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT username, realname, company, email FROM user WHERE id = %s', (user_id))
    user = cursor.fetchone()

    if not user:
        return "사용자를 찾을 수 없습니다.", 404

    return render_template('auth/user_profile.html', user=user)

#아이디 찾기
@bp.route('/find_id', methods=['GET', 'POST'])
def find_id():
    if request.method == 'POST':
        realname = request.form['realname']
        company = request.form['company']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'SELECT * FROM user WHERE realname = %s AND company = %s',
            (realname, company)
        )
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            flash(f"아이디는 '{user['username']}' 입니다.")
        else:
            flash("일치하는 사용자 정보가 없습니다.")

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

            # 이메일 전송 준비
            msg = MIMEText(f"임시 비밀번호: {temp_pw}\n로그인 후 반드시 비밀번호를 변경해주세요.")
            msg['Subject'] = "임시 비밀번호 발급 안내"
            msg['From'] = "wjdtnsgh386@gmail.com"    # 본인 Gmail 주소
            msg['To'] = email

            # 이메일 전송
            s = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            s.login("wjdtnsgh386@gmail.com", "tasg sgfi feth pqfa")  # 앱 비밀번호 사용
            s.send_message(msg)
            s.quit()

            flash("임시 비밀번호가 이메일로 전송되었습니다. 로그인 후 꼭 변경하세요!")
        else:
            flash("일치하는 회원 정보가 없습니다.")

    return render_template('auth/find_pw.html')

@bp.route('/change_pw', methods=['GET', 'POST'])
def change_pw():
    if request.method == 'POST':
        current_pw = request.form['current_password']
        new_pw = request.form['new_password']
        new_pw_confirm = request.form['new_password_confirm']

        db = get_db()
        cursor = db.cursor()

        user_id = session.get('user_id')  # 로그인 시 저장된 사용자 id
        cursor.execute('SELECT * FROM user WHERE id = %s', (user_id))
        user = cursor.fetchone()

        # 현재 비밀번호 확인
        if not check_password_hash(user['password'], current_pw):
            flash("현재 비밀번호가 일치하지 않습니다.")
            return redirect(url_for('auth.edit_profile'))

        # 새 비밀번호와 확인 값 비교
        if new_pw != new_pw_confirm:
            flash("새 비밀번호와 확인 값이 일치하지 않습니다.")
            return redirect(url_for('auth.edit_profile'))

        # 새 비밀번호 해시화 후 DB에 저장
        new_pw_hash = generate_password_hash(new_pw)
        cursor.execute('UPDATE user SET password = %s WHERE id = %s', (new_pw_hash, user_id))
        db.commit()

        flash("비밀번호가 성공적으로 변경되었습니다!")
        return redirect(url_for('auth.edit_profile'))

    return render_template('auth/change_pw.html')