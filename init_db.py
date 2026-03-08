# -*- coding: utf-8 -*-
"""初始化数据库并创建管理员账号"""
import sys
sys.path.insert(0, '.')

from app import app
from backend.models import db, User
from backend.crawler.base_crawler import BaseCrawler


def init():
    with app.app_context():
        db.create_all()
        
        # 创建默认管理员
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('管理员账号已创建: admin / admin123')
        
        # 创建示例数据（若数据库为空）
        BaseCrawler.create_sample_data()


if __name__ == '__main__':
    init()
    print('数据库初始化完成')
