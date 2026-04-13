# -*- coding: utf-8 -*-
"""管理员API - 用户管理、Bug查看、爬虫数据管理"""
from flask import request, jsonify
from flask_login import login_required, current_user
from backend.routes import api_bp
from backend.models import (
    db, User, BugFeedback,
    CPU, Motherboard, GPU, Memory, SSD, Cooling, Case, PSU
)

COMPONENT_MODELS = {
    'cpu': CPU, 'motherboard': Motherboard, 'gpu': GPU, 'memory': Memory,
    'ssd': SSD, 'cooling': Cooling, 'case': Case, 'psu': PSU
}


def admin_required(f):
    """管理员权限装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'success': False, 'msg': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated


# ========== 用户管理 ==========
@api_bp.route('/admin/users', methods=['GET'])
@login_required
@admin_required
def list_users():
    """用户列表"""
    users = User.query.all()
    return jsonify({
        'success': True,
        'data': [{'id': u.id, 'username': u.username, 'is_admin': u.is_admin, 'created_at': u.created_at.isoformat()} for u in users]
    })


@api_bp.route('/admin/users', methods=['POST'])
@login_required
@admin_required
def add_user():
    """添加用户"""
    data = request.get_json()
    username = (data.get('username') or '').strip()
    password = data.get('password', '')
    is_admin = bool(data.get('is_admin', False))
    
    if not username or not password:
        return jsonify({'success': False, 'msg': '用户名和密码不能为空'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'msg': '用户名已存在'}), 400
    
    user = User(username=username, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'msg': '添加成功', 'id': user.id})


@api_bp.route('/admin/users/<int:uid>', methods=['PUT'])
@login_required
@admin_required
def update_user(uid):
    """更新用户"""
    user = User.query.get_or_404(uid)
    data = request.get_json()
    
    if 'username' in data:
        uname = data['username'].strip()
        if uname and User.query.filter(User.username == uname, User.id != uid).first() is None:
            user.username = uname
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    if 'is_admin' in data:
        user.is_admin = bool(data['is_admin'])
    
    db.session.commit()
    return jsonify({'success': True, 'msg': '更新成功'})


@api_bp.route('/admin/users/<int:uid>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(uid):
    """删除用户"""
    if uid == current_user.id:
        return jsonify({'success': False, 'msg': '不能删除自己'}), 400
    
    user = User.query.get_or_404(uid)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True, 'msg': '删除成功'})


# ========== Bug反馈管理 ==========
@api_bp.route('/admin/bugs', methods=['GET'])
@login_required
@admin_required
def list_all_bugs():
    """管理员查看所有Bug反馈"""
    feedbacks = BugFeedback.query.order_by(BugFeedback.created_at.desc()).all()
    users = {u.id: u.username for u in User.query.all()}
    
    return jsonify({
        'success': True,
        'data': [{
            'id': f.id, 'title': f.title, 'content': f.content,
            'status': f.status, 'username': users.get(f.user_id, ''),
            'created_at': f.created_at.isoformat()
        } for f in feedbacks]
    })


@api_bp.route('/admin/bugs/<int:bid>', methods=['PUT'])
@login_required
@admin_required
def update_bug_status(bid):
    """更新Bug状态"""
    feedback = BugFeedback.query.get_or_404(bid)
    data = request.get_json()
    if 'status' in data and data['status'] in ('pending', 'resolved'):
        feedback.status = data['status']
    db.session.commit()
    return jsonify({'success': True, 'msg': '更新成功'})


# ========== 爬虫数据管理（各配件增删改） ==========
@api_bp.route('/admin/components/<component>', methods=['GET'])
@login_required
@admin_required
def list_components(component):
    """获取某类配件列表"""
    import sqlite3
    import os
    from config import Config

    table_map = {
        'cpu': 'cpu_analyzed', 'motherboard': '主板_analyzed', 'gpu': '显卡_analyzed',
        'memory': '内存条_analyzed', 'ssd': '固态_analyzed', 'cooling': '散热_analyzed',
        'case': '机箱_analyzed', 'psu': '电源_analyzed'
    }
    table_name = table_map.get(component)
    if not table_name:
        return jsonify({'success': False, 'msg': '未知配件类型'}), 400

    db_path = os.path.join(Config.BASE_DIR, 'data', 'ai_analyzed.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute(f"PRAGMA table_info({table_name})")
        cols = [c['name'] for c in cur.fetchall() if c['name'] != 'id']

        price_col = '商品价格' if '商品价格' in cols else '价格'

        cur.execute(f"SELECT * FROM {table_name} ORDER BY CAST({price_col} AS REAL) ASC LIMIT 100")
        rows = cur.fetchall()

        data = []
        for row in rows:
            item = {'id': row['id']}
            for col in cols:
                val = row[col]
                if component == 'memory' and col == '商品名称' and isinstance(val, str):
                    if ' - ' in val:
                        val = val.split(' - ')[-1].strip()
                    words = val.split()
                    half = len(words) // 2
                    if half > 0 and words[:half] == words[half:]:
                        val = ' '.join(words[:half])
                item[col] = val
            data.append(item)

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'msg': str(e)}), 500
    finally:
        conn.close()


@api_bp.route('/admin/components/<component>', methods=['POST'])
@login_required
@admin_required
def add_component(component):
    """添加配件"""
    import sqlite3
    import os
    from config import Config
    table_map = {
        'cpu': 'cpu_analyzed', 'motherboard': '主板_analyzed', 'gpu': '显卡_analyzed',
        'memory': '内存条_analyzed', 'ssd': '固态_analyzed', 'cooling': '散热_analyzed',
        'case': '机箱_analyzed', 'psu': '电源_analyzed'
    }
    table_name = table_map.get(component)
    if not table_name:
        return jsonify({'success': False, 'msg': '未知配件类型'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'msg': '无数据'}), 400

    db_path = os.path.join(Config.BASE_DIR, 'data', 'ai_analyzed.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        cur.execute(f"PRAGMA table_info({table_name})")
        valid_cols = [c[1] for c in cur.fetchall() if c[1] != 'id']

        keys = []
        values = []
        placeholders = []
        for k, v in data.items():
            if k in valid_cols:
                keys.append(f"[{k}]")
                values.append(v)
                placeholders.append('?')

        if not keys:
            return jsonify({'success': False, 'msg': '没有有效字段'}), 400

        sql = f"INSERT INTO {table_name} ({','.join(keys)}) VALUES ({','.join(placeholders)})"
        cur.execute(sql, tuple(values))
        conn.commit()
        return jsonify({'success': True, 'msg': '添加成功', 'id': cur.lastrowid})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'msg': str(e)}), 500
    finally:
        conn.close()


@api_bp.route('/admin/components/<component>/<int:cid>', methods=['PUT'])
@login_required
@admin_required
def update_component(component, cid):
    """更新配件"""
    import sqlite3
    import os
    from config import Config
    table_map = {
        'cpu': 'cpu_analyzed', 'motherboard': '主板_analyzed', 'gpu': '显卡_analyzed',
        'memory': '内存条_analyzed', 'ssd': '固态_analyzed', 'cooling': '散热_analyzed',
        'case': '机箱_analyzed', 'psu': '电源_analyzed'
    }
    table_name = table_map.get(component)
    if not table_name:
        return jsonify({'success': False, 'msg': '未知配件类型'}), 400

    data = request.get_json()
    db_path = os.path.join(Config.BASE_DIR, 'data', 'ai_analyzed.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        cur.execute(f"PRAGMA table_info({table_name})")
        valid_cols = [c[1] for c in cur.fetchall() if c[1] != 'id']

        set_clause = []
        values = []
        for k, v in data.items():
            if k in valid_cols:
                set_clause.append(f"[{k}]=?")
                values.append(v)

        if not set_clause:
            return jsonify({'success': True, 'msg': '无更新内容'})

        values.append(cid)
        sql = f"UPDATE {table_name} SET {','.join(set_clause)} WHERE id=?"
        cur.execute(sql, tuple(values))
        conn.commit()
        return jsonify({'success': True, 'msg': '更新成功'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'msg': str(e)}), 500
    finally:
        conn.close()


@api_bp.route('/admin/components/<component>/<int:cid>', methods=['DELETE'])
@login_required
@admin_required
def delete_component(component, cid):
    """删除配件"""
    import sqlite3
    import os
    from config import Config
    table_map = {
        'cpu': 'cpu_analyzed', 'motherboard': '主板_analyzed', 'gpu': '显卡_analyzed',
        'memory': '内存条_analyzed', 'ssd': '固态_analyzed', 'cooling': '散热_analyzed',
        'case': '机箱_analyzed', 'psu': '电源_analyzed'
    }
    table_name = table_map.get(component)
    if not table_name:
        return jsonify({'success': False, 'msg': '未知配件类型'}), 400

    db_path = os.path.join(Config.BASE_DIR, 'data', 'ai_analyzed.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute(f"DELETE FROM {table_name} WHERE id=?", (cid,))
        conn.commit()
        return jsonify({'success': True, 'msg': '删除成功'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'msg': str(e)}), 500
    finally:
        conn.close()
