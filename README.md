import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).resolve().parent  # 定义项目的根目录
    # 其他配置项...# 基于Python的个性化电脑配置推荐系统

## 项目简介

本系统是一个基于Python开发的电脑硬件配置个性化推荐平台，能够根据用户预算和使用场景（办公/游戏/自定义）智能推荐最优配置方案，并整合京东、淘宝等电商平台的实时低价链接。

## 功能特性

### 前端功能
- **注册登录**：用户注册、登录、权限管理
- **普通用户**：配置推荐对话框、Bug反馈
- **管理员**：用户管理、爬虫数据管理、Bug反馈查看

### 后端功能
- **爬虫模块**：爬取京东/淘宝CPU、主板、显卡、内存、固态、散热、机箱、电源等配件低价链接
- **配置推荐算法**：办公/游戏/自定义三种预算分配模式
- **数据库**：各配件独立表存储，用户信息管理

## 技术栈

- **后端**：Python Flask + SQLAlchemy
- **数据库**：SQLite（可切换MySQL）
- **前端**：HTML + CSS + JavaScript
- **爬虫**：Requests + Selenium + BeautifulSoup

## 项目结构

```
biyesheji/
├── app.py                 # 应用入口
├── config.py              # 配置文件
├── requirements.txt       # 依赖
├── backend/               # 后端模块
│   ├── __init__.py
│   ├── models.py          # 数据库模型
│   ├── routes/            # API路由
│   ├── crawler/           # 爬虫模块
│   └── algorithm/         # 推荐算法
├── frontend/              # 前端静态文件
│   ├── static/
│   └── templates/
└── data/                  # 数据目录
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 初始化数据库
```bash
python init_db.py
```

### 3. 运行爬虫（可选，获取数据）
```bash
python run_crawler.py
```

### 4. 启动应用
```bash
python app.py
```

访问 http://127.0.0.1:5000

## 默认账号

- 管理员：admin / admin123
- 普通用户：需注册

## 注意事项

- 京东/淘宝有反爬机制，爬虫可能需要配置代理或使用Selenium
- 首次使用建议先运行爬虫获取数据，或使用系统内置的示例数据
