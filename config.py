# -*- coding: utf-8 -*-
"""系统配置文件"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'pc-config-recommend-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/data/pc_config.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 预算分配 - 办公模式
    OFFICE_BUDGET = {
        'cpu': (20, 25),
        'gpu': (20, 25),
        'motherboard': (10, 15),
        'memory': (10, 20),
        'ssd': (8, 15),
        'psu': (5, 8),
        'cooling': (3, 5),
        'case': (3, 5),
    }
    
    # 预算分配 - 游戏模式
    GAMING_BUDGET = {
        'cpu': (10, 15),
        'gpu': (30, 40),
        'motherboard': (5, 10),
        'memory': (10, 20),
        'ssd': (5, 10),
        'psu': (5, 8),
        'cooling': (3, 5),
        'case': (3, 5),
    }
