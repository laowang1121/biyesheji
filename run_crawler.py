# -*- coding: utf-8 -*-
"""运行爬虫 - 爬取京东/淘宝硬件数据
注意：京东和淘宝有反爬机制，实际爬取可能需要：
1. 使用Selenium模拟浏览器
2. 配置代理IP池
3. 使用官方API（如有）
当前脚本会创建示例数据供开发测试"""
import sys
sys.path.insert(0, '.')

from app import app
from backend.crawler.base_crawler import BaseCrawler


if __name__ == '__main__':
    with app.app_context():
        print('开始创建/更新数据...')
        BaseCrawler.create_sample_data()
        print('完成。如需真实爬取，请扩展 backend/crawler/jd_crawler.py 并配置Selenium。')
