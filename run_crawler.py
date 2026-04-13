# -*- coding: utf-8 -*-
"""运行真实爬虫 - 使用 Selenium 爬取京东硬件数据"""
import sys
import os
import traceback

# --- 网络设置调整 ---
# 强制禁用代理设置，解决 "ConnectionRefusedError: 127.0.0.1:7890" 问题
# 因为您的代理软件可能没开，但环境变量里还有残留，必须手动清除
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

sys.path.insert(0, '.')

from app import app


if __name__ == '__main__':
    with app.app_context():
        print('Step 1: 开始运行真实爬虫脚本...')

        # 实例化爬虫对象
        try:
            print('Step 2: 准备实例化 JDCrawler...')
            crawler = JDCrawler()
            
            print('Step 3: 实例化完成，开始调用 crawl_all...')
            # 调用爬取入口方法
            crawler.crawl_all(app)
            print('Step 4: 真实爬取测试完毕！')
        except Exception as e:
            print(f"运行出错: {e}")
            print("=== 错误详情 ===")
            traceback.print_exc()
            
            # 如果是驱动问题，给出明确提示
            if "SessionNotCreatedException" in str(e) or "executable needs to be in PATH" in str(e):
                print("\n💡 提示：请尝试先运行 download_driver.py 更新驱动。")
