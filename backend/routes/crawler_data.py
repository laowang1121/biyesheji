# -*- coding: utf-8 -*-
"""爬虫数据相关 - 触发爬虫、查看爬虫状态"""
from flask import jsonify
from flask_login import login_required, current_user
from backend.routes import api_bp
from backend.models import CPU, Motherboard, GPU, Memory, SSD, Cooling, Case, PSU


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'success': False, 'msg': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated


@api_bp.route('/admin/crawler/stats', methods=['GET'])
@login_required
@admin_required
def crawler_stats():
    """各配件数据统计"""
    models = {
        'cpu': CPU, 'motherboard': Motherboard, 'gpu': GPU, 'memory': Memory,
        'ssd': SSD, 'cooling': Cooling, 'case': Case, 'psu': PSU
    }
    stats = {k: v.query.count() for k, v in models.items()}
    return jsonify({'success': True, 'data': stats})
