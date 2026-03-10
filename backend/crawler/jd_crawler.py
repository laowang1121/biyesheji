# -*- coding: utf-8 -*-
"""京东爬虫 - 使用 Selenium 爬取各硬件低价链接"""
import time
import os
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote

from backend.crawler.base_crawler import BaseCrawler
from backend.models import db, CPU  # 这里先以CPU为例测试，您可以引入其他硬件模型


class JDCrawler():
    """京东硬件真实爬虫"""

    CPU_KEYWORDS = ['AMD 锐龙5', 'Intel 酷睿 i5']

    def __init__(self):
        super().__init__()
        print("--> [DEBUG] JDCrawler 初始化开始") # 添加日志

        # 配置无头浏览器 (Selenium)
        chrome_options = Options()
        # 生产环境/不希望看到浏览器弹窗可以取消注释下面这行：
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage') # 增加这行防止内存共享不足
        
        # --- 关键修改：寻找并指定 Chrome 浏览器程序路径 ---
        # 报错 "cannot find Chrome binary" 是因为这里没设置好
        found_binary = False
        possible_chrome_paths = [
            r"I:\ruanjian\Google\Chrome\Application\chrome.exe", # 您之前代码里注释掉的路径
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"D:\Program Files\Google\Chrome\Application\chrome.exe",
        ]
        
        for path in possible_chrome_paths:
            if os.path.exists(path):
                print(f"--> [DEBUG] 找到浏览器程序: {path}")
                chrome_options.binary_location = path
                found_binary = True
                break
        
        if not found_binary:
            print("--> [WARNING] 未能在常见路径找到 chrome.exe，将尝试使用系统默认路径...")
            print("    如果再次报错，请在 possible_chrome_paths 列表中手动填入您的 chrome.exe 绝对路径。")
        # ----------------------------------------------------

        driver_path = None

        # 1. 优先检查本地是否存在 chromedriver.exe (避免每次运行都在这里卡顿或报错)
        print("--> [DEBUG] 正在寻找本地 chromedriver.exe ...")
        possible_paths = [
            "chromedriver.exe",
            os.path.join(os.getcwd(), "chromedriver.exe"),
            os.path.join(os.path.dirname(sys.executable), "chromedriver.exe"),
            r"I:\pycharm\PycharmProjects\biyesheji\.venv\Scripts\chromedriver.exe"
        ]
        for p in possible_paths:
            if os.path.exists(p):
                driver_path = os.path.abspath(p)
                print(f"--> [DEBUG] 成功找到本地驱动: {driver_path}")
                break

        # 2. 如果本地找不到，才尝试自动联网下载
        if not driver_path:
            print("--> [DEBUG] 本地未找到，尝试联网下载 Chrome 驱动...")
            try:
                driver_path = ChromeDriverManager(
                    url="https://registry.npmmirror.com/-/binary/chromedriver",
                    latest_release_url="https://registry.npmmirror.com/-/binary/chromedriver/LATEST_RELEASE"
                ).install()
                print(f"--> [DEBUG] 自动下载驱动成功: {driver_path}")
            except Exception as e:
                print(f"--> [ERROR] 驱动下载失败: {e}")
                # 不再抛出异常，继续往下走看看能不能通过某种神奇方式运行，或者最终在下面报错

        # 3. 最终检查
        if not driver_path:
            error_msg = (
                "\n无法获取 chromedriver！\n"
                "请确认您已将 chromedriver.exe 放在项目根目录: I:\\pycharm\\PycharmProjects\\biyesheji\\ \n"
            )
            print(error_msg)
            raise FileNotFoundError("没有找到 chromedriver.exe")

        print("--> [DEBUG] 正在启动浏览器进程...")
        self.driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
        print("--> [DEBUG] 浏览器启动成功！")

    def search_jd_real(self, keyword: str, limit: int = 5) -> list:
        """使用 Selenium 执行真实的京东搜索"""
        print(f"正在京东真实爬取: {keyword}")
        url = f'https://search.jd.com/Search?keyword={quote(keyword)}&enc=utf-8'
        self.driver.get(url)

        # 等待页面中的商品列表元素加载出来，最长等待 10 秒
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'gl-item'))
            )
        except Exception as e:
            print(f"等待商品列表加载失败: {e}")
            return []

        # 稍微往下滚动，触发图片和价格动态加载
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)

        html = self.driver.page_source
        return self._parse_jd_html(html, limit)

    def _parse_jd_html(self, html: str, limit: int) -> list:
        """解析抓取回来的 HTML 内容"""
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('li', class_='gl-item')
        results = []

        for item in items[:limit]:
            try:
                # 提取价格
                price_tag = item.find('div', class_='p-price')
                price_text = price_tag.find('i').text if price_tag and price_tag.find('i') else '0'
                price = float(price_text) if price_text != '0' else 0.0

                # 提取商品名称
                name_tag = item.find('div', class_='p-name')
                name = name_tag.find('em').text.strip() if name_tag else '未知商品'

                # 提取链接
                link_tag = item.find('div', class_='p-img').find('a')
                link = link_tag['href'] if link_tag else ''
                if link and not link.startswith('http'):
                    link = 'https:' + link

                results.append({
                    'name': name,
                    'price': price,
                    'link': link,
                    'source': 'jd'
                })
            except Exception as e:
                print(f"解析单个商品出错: {e}")
                continue

        return results

    def crawl_all(self, app):
        """执行全量爬取并入库"""
        with app.app_context():
            print("=== 开始真实爬取京东数据 ===")
            for keyword in self.CPU_KEYWORDS:
                data_list = self.search_jd_real(keyword, limit=3)
                for data in data_list:
                    print(f"爬取到: {data['name']} - ￥{data['price']}")
                    # 在此处执行入库：判断是否有重名，没有则插入
                    # 示例只写入了最基本的字段，你需要结合 model 补全必填字段
                    cpu = CPU(
                        brand='Intel' if 'Intel' in keyword else 'AMD',
                        model=data['name'][:20],  # 截断用于示例
                        series=keyword,
                        package_type='盒装',
                        price=data['price'],
                        link=data['link'],
                        source='jd'
                    )
                    self.save_item(CPU, cpu.__dict__)
            print("=== 真实爬取完成 ===")
            self.driver.quit()

    def save_item(self, model_class, item_data: dict):
        """保存单条数据"""
        try:
            # 去除 SQLAlchemy 的内部状态属性
            item_data.pop('_sa_instance_state', None)
            obj = model_class(**item_data)
            db.session.add(obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"保存失败: {e}")
