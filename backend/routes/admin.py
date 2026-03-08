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
    Model = COMPONENT_MODELS.get(component)
    if not Model:
        return jsonify({'success': False, 'msg': '未知配件类型'}), 400
    
    items = Model.query.order_by(Model.price.asc()).limit(100).all()
    cols = [c.key for c in Model.__table__.columns if c.key not in ('id', 'created_at')]
    
    return jsonify({
        'success': True,
        'data': [{k: getattr(i, k) for k in cols} | {'id': i.id} for i in items]
    })


@api_bp.route('/admin/components/<component>', methods=['POST'])
@login_required
@admin_required
def add_component(component):
    """添加配件"""
    Model = COMPONENT_MODELS.get(component)
    if not Model:
        return jsonify({'success': False, 'msg': '未知配件类型'}), 400
    
    data = request.get_json()
    required = {'brand', 'model', 'price'}
    if not required.issubset(data.keys()):
        return jsonify({'success': False, 'msg': f'缺少必填字段: {required - set(data.keys())}'}), 400
    
    # 过滤有效字段
    valid_cols = {c.key for c in Model.__table__.columns if c.key != 'id'}
    item_data = {k: v for k, v in data.items() if k in valid_cols}
    
    obj = Model(**item_data)
    db.session.add(obj)
    db.session.commit()
    return jsonify({'success': True, 'msg': '添加成功', 'id': obj.id})


@api_bp.route('/admin/components/<component>/<int:cid>', methods=['PUT'])
@login_required
@admin_required
def update_component(component, cid):
    """更新配件"""
    Model = COMPONENT_MODELS.get(component)
    if not Model:
        return jsonify({'success': False, 'msg': '未知配件类型'}), 400
    
    obj = Model.query.get_or_404(cid)
    data = request.get_json()
    valid_cols = {c.key for c in Model.__table__.columns if c.key not in ('id',)}
    
    for k, v in data.items():
        if k in valid_cols and hasattr(obj, k):
            setattr(obj, k, v)
    
    db.session.commit()
    return jsonify({'success': True, 'msg': '更新成功'})


@api_bp.route('/admin/components/<component>/<int:cid>', methods=['DELETE'])
@login_required
@admin_required
def delete_component(component, cid):
    """删除配件"""
    Model = COMPONENT_MODELS.get(component)
    if not Model:
        return jsonify({'success': False, 'msg': '未知配件类型'}), 400
    
    obj = Model.query.get_or_404(cid)
    db.session.delete(obj)
    db.session.commit()
    return jsonify({'success': True, 'msg': '删除成功'})
