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
    import sqlite3
    import os
    from config import Config

    models = {
        'cpu': 'cpu_analyzed', 'motherboard': '主板_analyzed', 'gpu': '显卡_analyzed',
        'memory': '内存条_analyzed', 'ssd': '固态_analyzed', 'cooling': '散热_analyzed',
        'case': '机箱_analyzed', 'psu': '电源_analyzed'
    }
    db_path = os.path.join(Config.BASE_DIR, 'data', 'ai_analyzed.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    stats = {}
    for k, table in models.items():
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            stats[k] = cur.fetchone()[0]
        except Exception:
            stats[k] = 0
    conn.close()

    return jsonify({'success': True, 'data': stats})
