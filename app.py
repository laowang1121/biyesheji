# -*- coding: utf-8 -*-
"""应用入口"""
import os
from pathlib import Path
from flask import Flask, render_template, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, current_user

from config import Config, BASE_DIR
from backend.models import db, User
from backend.routes import api_bp

# 确保数据目录存在
Path(BASE_DIR / 'data').mkdir(exist_ok=True)

app = Flask(__name__, static_folder='frontend/static', template_folder='frontend/templates')
app.config.from_object(Config)
CORS(app, supports_credentials=True)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.session_protection = 'strong'


@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid)) if uid else None


@login_manager.unauthorized_handler
def unauthorized():
    from flask import request
    if request.path.startswith('/api/'):
        from flask import jsonify
        return jsonify({'success': False, 'msg': '请先登录'}), 401
    return redirect(url_for('login_page'))


app.register_blueprint(api_bp)


# ========== 页面路由 ==========
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('login_page'))


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/home')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login_page'))
    if current_user.is_admin:
        return render_template('admin.html')
    return render_template('user.html')


@app.route('/logout')
def logout():
    from flask_login import logout_user
    logout_user()
    return redirect(url_for('login_page'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
