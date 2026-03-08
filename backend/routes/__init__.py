# -*- coding: utf-8 -*-
"""API路由模块"""
from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from backend.routes import auth, user, admin, recommend, bug, crawler_data
