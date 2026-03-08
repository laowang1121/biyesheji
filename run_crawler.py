# -*- coding: utf-8 -*-
"""运行真实爬虫 - 使用 Selenium 爬取京东硬件数据"""
import sys
import os

# --- 强制网络修复开始 ---
# 1. 设置 NO_PROXY 为 *，这是最关键的一步，告诉 requests/urllib3 对所有地址都不使用代理
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# 2. 为了双重保险，将显式代理设置为空字符串
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
# --- 强制网络修复结束 ---

sys.path.insert(0, '.')

from app import app
from backend.crawler.jd_crawler import JDCrawler

if __name__ == '__main__':
    with app.app_context():
        print('开始运行真实爬虫...')

        # 实例化爬虫对象（这一步会下载 chromedriver，现在应该不会走代理了）
        try:
            crawler = JDCrawler()
            # 调用爬取入口方法
            crawler.crawl_all(app)
            print('真实爬取测试完毕！')
        except Exception as e:
            print(f"运行出错: {e}")