# -*- coding: utf-8 -*-
"""配置推荐API"""
from flask import request, jsonify
from flask_login import login_required
from backend.routes import api_bp
from backend.algorithm.recommender import ConfigRecommender


@api_bp.route('/recommend', methods=['POST'])
@login_required
def recommend():
    """
    配置推荐
    Body: { budget: 5000, mode: 'office'|'gaming'|'custom', custom_allocation?: {...} }
    """
    data = request.get_json() or {}
    budget = float(data.get('budget', 5000))
    mode = data.get('mode', 'office')
    custom_allocation = data.get('custom_allocation')
    
    if budget <= 0 or budget > 100000:
        return jsonify({'success': False, 'msg': '预算需在1-100000元之间'}), 400
    
    try:
        if mode == 'custom' and custom_allocation:
            valid, err = ConfigRecommender.validate_custom_allocation(custom_allocation)
            if not valid:
                return jsonify({'success': False, 'msg': err}), 400
        
        recommender = ConfigRecommender(budget, mode, custom_allocation)
        result = recommender.recommend()
        return jsonify({'success': True, 'data': result})
    except ValueError as e:
        return jsonify({'success': False, 'msg': str(e)}), 400


@api_bp.route('/recommend/budget-presets', methods=['GET'])
def get_budget_presets():
    """获取预算预设（办公/游戏分配说明）"""
    return jsonify({
        'success': True,
        'office': {
            'cpu': '20-25%', 'gpu': '20-25%', 'motherboard': '10-15%', 'memory': '10-20%',
            'ssd': '8-15%', 'psu': '5-8%', 'cooling': '3-5%', 'case': '3-5%'
        },
        'gaming': {
            'cpu': '10-15%', 'gpu': '30-40%', 'motherboard': '5-10%', 'memory': '10-20%',
            'ssd': '5-10%', 'psu': '5-8%', 'cooling': '3-5%', 'case': '3-5%'
        }
    })
