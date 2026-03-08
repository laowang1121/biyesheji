# -*- coding: utf-8 -*-
"""认证相关API"""
from flask import request, jsonify
from backend.routes import api_bp
from backend.models import db, User


@api_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'msg': '用户名和密码不能为空'}), 400
    
    if len(username) < 3:
        return jsonify({'success': False, 'msg': '用户名至少3个字符'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'msg': '用户名已存在'}), 400
    
    user = User(username=username, is_admin=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'msg': '注册成功', 'user_id': user.id})


@api_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    from flask_login import login_user
    
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'msg': '用户名或密码错误'}), 401
    
    login_user(user, remember=True)
    return jsonify({
        'success': True,
        'msg': '登录成功',
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin
        }
    })
