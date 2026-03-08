# -*- coding: utf-8 -*-
"""Bug反馈API"""
from flask import request, jsonify
from flask_login import login_required, current_user
from backend.routes import api_bp
from backend.models import db, BugFeedback


@api_bp.route('/bug/submit', methods=['POST'])
@login_required
def submit_bug():
    """提交Bug反馈"""
    data = request.get_json()
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    
    if not title or not content:
        return jsonify({'success': False, 'msg': '标题和内容不能为空'}), 400
    
    feedback = BugFeedback(
        user_id=current_user.id,
        title=title,
        content=content
    )
    db.session.add(feedback)
    db.session.commit()
    
    return jsonify({'success': True, 'msg': '反馈提交成功', 'id': feedback.id})


@api_bp.route('/bug/list', methods=['GET'])
@login_required
def list_my_bugs():
    """普通用户查看自己的反馈"""
    feedbacks = BugFeedback.query.filter_by(user_id=current_user.id).order_by(BugFeedback.created_at.desc()).all()
    return jsonify({
        'success': True,
        'data': [{
            'id': f.id, 'title': f.title, 'content': f.content,
            'status': f.status, 'created_at': f.created_at.isoformat()
        } for f in feedbacks]
    })
