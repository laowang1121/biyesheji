# -*- coding: utf-8 -*-
"""数据库模型定义"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class BugFeedback(db.Model):
    """Bug反馈表"""
    __tablename__ = 'bug_feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('feedbacks', lazy=True))


# ============ 硬件配件表 ============

class CPU(db.Model):
    """CPU表 - AMD锐龙系列、英特尔酷睿系列（散片/盒装）"""
    __tablename__ = 'cpus'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)  # AMD, Intel
    model = db.Column(db.String(200), nullable=False)
    series = db.Column(db.String(100))  # 锐龙系列, 酷睿系列
    package_type = db.Column(db.String(50))  # 散片, 盒装
    price = db.Column(db.Float, nullable=False)
    link = db.Column(db.String(500))
    source = db.Column(db.String(50))  # jd, taobao
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Motherboard(db.Model):
    """主板表 - 华硕、微星、华擎、铭瑄"""
    __tablename__ = 'motherboards'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(200), nullable=False)
    socket = db.Column(db.String(50))  # 对应CPU插槽
    price = db.Column(db.Float, nullable=False)
    link = db.Column(db.String(500))
    source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class GPU(db.Model):
    """显卡表 - AMD 6000/7000/9000, NVIDIA 4000/5000, Intel B500"""
    __tablename__ = 'gpus'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(200), nullable=False)
    series = db.Column(db.String(100))  # 6000系列, 7000系列, 4000系列等
    chip_brand = db.Column(db.String(50))  # AMD, NVIDIA, Intel
    price = db.Column(db.Float, nullable=False)
    link = db.Column(db.String(500))
    source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Memory(db.Model):
    """内存表 - DDR4/DDR5 各品牌最低10个链接"""
    __tablename__ = 'memories'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # DDR4, DDR5
    capacity = db.Column(db.String(50))  # 16G, 32G等
    price = db.Column(db.Float, nullable=False)
    link = db.Column(db.String(500))
    source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SSD(db.Model):
    """固态硬盘表 - PCIe3.0/4.0 500G-1T 各容量最低10个"""
    __tablename__ = 'ssds'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(200), nullable=False)
    interface = db.Column(db.String(20), nullable=False)  # PCIe3.0, PCIe4.0
    capacity = db.Column(db.String(50), nullable=False)  # 500G, 1T
    price = db.Column(db.Float, nullable=False)
    link = db.Column(db.String(500))
    source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Cooling(db.Model):
    """散热表 - 风冷100元5款，水冷240/360各200-500元10款"""
    __tablename__ = 'coolings'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 风冷, 水冷240, 水冷360
    price = db.Column(db.Float, nullable=False)
    link = db.Column(db.String(500))
    source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Case(db.Model):
    """机箱表 - 50元1款，100-300元海景房5款+非海景房5款"""
    __tablename__ = 'cases'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(200), nullable=False)
    style = db.Column(db.String(50))  # 海景房, 普通
    price = db.Column(db.Float, nullable=False)
    link = db.Column(db.String(500))
    source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PSU(db.Model):
    """电源表 - 海韵、振华 各规格1款"""
    __tablename__ = 'psus'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)  # 海韵, 振华
    model = db.Column(db.String(200), nullable=False)
    wattage = db.Column(db.String(20), nullable=False)  # 450W, 550W, 650W, 750W, 850W
    certification = db.Column(db.String(50))  # 金牌全模组
    price = db.Column(db.Float, nullable=False)
    link = db.Column(db.String(500))
    source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
