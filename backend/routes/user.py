# -*- coding: utf-8 -*-
"""用户相关API"""
from flask import jsonify
from flask_login import login_required, current_user
from backend.routes import api_bp


@api_bp.route('/user/me', methods=['GET'])
@login_required
def get_current_user():
    """获取当前登录用户信息"""
    return jsonify({
        'success': True,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'is_admin': current_user.is_admin
        }
    })
