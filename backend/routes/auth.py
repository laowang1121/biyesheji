# -*- coding: utf-8 -*-
"""认证相关API"""
from flask import request, jsonify
from backend.routes import api_bp
from backend.models import db, User

# 新增导入
from flask import session, make_response
import io
import random
import string
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except Exception:
    # Pillow may not be installed yet; registration will still fail until dependencies are installed
    Image = ImageDraw = ImageFont = ImageFilter = None


@api_bp.route('/captcha')
def captcha():
    """生成验证码图片并存入 session，返回 PNG 图片"""
    # 生成4位随机验证码（字母+数字）
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    # 保存小写到session以便比较（不区分大小写）
    session['captcha'] = code.lower()

    # 如果 Pillow 不可用，返回纯文本图片不可用的提示图片或简单文本响应
    if Image is None:
        # 返回简单的 PNG with text using no external lib is complicated; return 204 to indicate no image
        return jsonify({'success': False, 'msg': 'captcha not available'}), 204

    width, height = 140, 50
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 载入字体（优先使用系统字体，否则使用默认字体）
    try:
        font = ImageFont.truetype('arial.ttf', 30)
    except Exception:
        font = ImageFont.load_default()

    # 绘制干扰线
    for i in range(5):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)), width=1)

    # 绘制验证码字符
    for i, ch in enumerate(code):
        x = 10 + i * 30 + random.randint(-3, 3)
        y = random.randint(0, 10)
        draw.text((x, y), ch, font=font, fill=(random.randint(0, 120), random.randint(0, 120), random.randint(0, 120)))

    # 可选滤镜
    try:
        img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    except Exception:
        pass

    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    resp = make_response(buf.getvalue())
    resp.headers.set('Content-Type', 'image/png')
    # 禁止缓存以确保每次刷新都能得到新图
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp


@api_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    # 新增验证码字段
    captcha_val = data.get('captcha', '').strip().lower()

    if not username or not password:
        return jsonify({'success': False, 'msg': '用户名和密码不能为空'}), 400

    # 验证验证码
    saved = session.get('captcha')
    # 清除 session 中的验证码，防止重放
    session.pop('captcha', None)
    if not saved or not captcha_val or captcha_val != saved:
        return jsonify({'success': False, 'msg': '验证码错误'}), 400

    if len(username) < 3:
        return jsonify({'success': False, 'msg': '用户名至少3个字符'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'msg': '用户名已存在'}), 400

    user = User(username=username, is_admin=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'success': True, 'msg': '注册成功', 'user_id': user.id})


@api_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    from flask_login import login_user

    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'msg': '用户名或密码错误'}), 401

    login_user(user, remember=True)
    return jsonify({
        'success': True,
        'msg': '登录成功',
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin
        }
    })
