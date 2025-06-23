from flask import Flask, g, render_template, session
from db import get_db
from routes.board_routes import bp as board_bp
from routes.post_routes import bp as post_bp
from routes.auth_routes import bp as auth_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db:
        db.close()

app.register_blueprint(board_bp)
app.register_blueprint(post_bp)
app.register_blueprint(auth_bp)

@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM board ORDER BY id DESC')
    boards = cursor.fetchall()
    return render_template('index.html', boards=boards, username=session.get('username'))

if __name__ == '__main__':
    app.run(debug=True)