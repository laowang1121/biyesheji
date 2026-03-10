# -*- coding: utf-8 -*-
"""京东爬虫 - 使用 Selenium 爬取各硬件低价链接"""
import time
import os
import sys
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import SessionNotCreatedException
from urllib.parse import quote

from backend.crawler.base_crawler import BaseCrawler
from backend.models import db, CPU  # 这里先以CPU为例测试，您可以引入其他硬件模型


class JDCrawler():
    """京东硬件真实爬虫"""

    CPU_KEYWORDS = ['AMD 锐龙5', 'Intel 酷睿 i5']

    def __init__(self):
        super().__init__()
        print("--> [DEBUG] JDCrawler 初始化开始")

        # 配置无头浏览器 (Selenium)
        chrome_options = Options()
        # 生产环境/不希望看到浏览器弹窗可以取消注释下面这行：
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # --- 新增：防反爬虫配置 ---
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        found_binary = False
        possible_chrome_paths = [
            r"I:\ruanjian\Google\Chrome\Application\chrome.exe",
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

        # --- 关键修改：不再自动下载，直接读取刚才手动替换好的本地驱动 ---
        print("--> [DEBUG] 正在读取本地 chromedriver.exe ...")

        driver_path = r"I:\pycharm\PycharmProjects\biyesheji\chromedriver.exe"

        if not os.path.exists(driver_path):
            print(f"--> [ERROR] 找不到驱动文件！请确保已将 chromedriver.exe 放在: {driver_path}")
            raise FileNotFoundError(f"找不到驱动文件: {driver_path}")

        print(f"--> [DEBUG] 成功找到本地驱动: {driver_path}")
        print("--> [DEBUG] 正在启动浏览器进程...")

        try:
            self.driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
            # 隐藏 navigator.webdriver 特征
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
                """
            })
            print("--> [DEBUG] 浏览器启动成功！")
        except SessionNotCreatedException as e:
            print("\n" + "=" * 50)
            print("❌ 启动失败：你本地的 chromedriver.exe 版本不对！")
            print("💡 解决方法：")
            print("   1. 打开网站: https://googlechromelabs.github.io/chrome-for-testing/")
            print("   2. 找到版本为 145.x 的 chromedriver 并下载")
            print(f"   3. 解压后，将其替换掉 I:\\pycharm\\PycharmProjects\\biyesheji\\chromedriver.exe")
            print(f"报错信息:\n{e.msg}")
            print("=" * 50 + "\n")
            raise e

    def load_cookies(self):
        """加载本地 Cookie"""
        cookie_path = 'jd_cookies.json'
        if os.path.exists(cookie_path):
            with open(cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            print("--> [INFO] 成功加载本地 Cookie！")
            return True
        return False

    def save_cookies(self):
        """保存当前 Cookie 到本地"""
        cookies = self.driver.get_cookies()
        with open('jd_cookies.json', 'w', encoding='utf-8') as f:
            json.dump(cookies, f)
        print("--> [INFO] Cookie 已保存到本地 jd_cookies.json")

    def search_jd_real(self, keyword: str, limit: int = 5) -> list:
        """使用 Selenium 执行真实的京东搜索"""
        print(f"正在京东真实爬取: {keyword}")
        url = f'https://search.jd.com/Search?keyword={quote(keyword)}&enc=utf-8'

        # 先访问一次京东域名才能植入 cookie
        self.driver.get('https://www.jd.com')
        if self.load_cookies():
            self.driver.refresh()
            time.sleep(1)

        self.driver.get(url)

        # 登录检测逻辑
        if "passport" in self.driver.current_url:
            print("--> [🛑 触发反爬] 京东要求登录或 Cookie 已失效！")
            print("--> [👉 操作提示] 请在弹出的浏览器窗口中，60秒内使用京东APP【扫码登录】...")

            # 给用户 60 秒时间手动扫码
            for i in range(60, 0, -1):
                if i % 10 == 0:
                    print(f"    剩余 {i} 秒...")
                if "passport" not in self.driver.current_url:
                    print("--> [✅ 状态] 检测到网址变化，登录成功！")
                    self.save_cookies()  # 登录成功后立刻保存 cookie
                    break
                time.sleep(1)

            if "passport" in self.driver.current_url:
                print("--> [⚠️ 超时] 似乎未完成登录，继续执行可能无法获取数据...")
            else:
                self.driver.get(url)  # 重新进入搜索页

        # 等待商品列表加载出来
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
                price_tag = item.find('div', class_='p-price')
                price_text = price_tag.find('i').text if price_tag and price_tag.find('i') else '0'
                price = float(price_text) if price_text != '0' else 0.0

                name_tag = item.find('div', class_='p-name')
                name = name_tag.find('em').text.strip() if name_tag else '未知商品'

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
                    cpu = CPU(
                        brand='Intel' if 'Intel' in keyword else 'AMD',
                        model=data['name'][:20],
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
            item_data.pop('_sa_instance_state', None)
            obj = model_class(**item_data)
            db.session.add(obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"保存失败: {e}")