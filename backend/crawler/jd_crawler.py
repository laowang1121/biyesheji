# -*- coding: utf-8 -*-
"""京东爬虫 - 使用 undetected_chromedriver 绕过反爬"""
import time
import os
import sys
import json
import random
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote

# 导入 undetected_chromedriver
import undetected_chromedriver as uc

from backend.crawler.base_crawler import BaseCrawler
from backend.models import db, CPU


class JDCrawler():
    """京东硬件真实爬虫"""

    CPU_KEYWORDS = ['AMD 锐龙5', 'Intel 酷睿 i5']

    def __init__(self):
        super().__init__()
        print("--> [DEBUG] JDCrawler 初始化开始")

        options = uc.ChromeOptions()
        # 禁用一些不必要的服务，减少被检测概率
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # 伪装 User-Agent (非常重要！)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f'user-agent={user_agent}')

        # 禁用提示框
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        options.add_experimental_option("prefs", prefs)

        found_binary = False
        possible_chrome_paths = [
            r"I:\ruanjian\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]

        for path in possible_chrome_paths:
            if os.path.exists(path):
                options.binary_location = path
                found_binary = True
                break

        driver_path = r"I:\pycharm\PycharmProjects\biyesheji\chromedriver.exe"

        print("--> [DEBUG] 正在启动 undetected_chromedriver ...")
        try:
            # 增加 version_main 参数，帮助 uc 更好地匹配你的 Chrome 版本
            self.driver = uc.Chrome(
                options=options,
                driver_executable_path=driver_path,
                version_main=120  # 假设你使用的是 Chrome 120，如果不对请根据实际情况修改
            )
            self.driver.implicitly_wait(10)

            # 进一步隐藏 webdriver 特征
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                      get: () => undefined
                    })
                """
            })
            print("--> [DEBUG] 浏览器启动成功！")
        except Exception as e:
            print(f"❌ 浏览器启动失败: {e}")
            raise e

    def load_cookies(self):
        cookie_path = 'jd_cookies.json'
        if os.path.exists(cookie_path):
            try:
                with open(cookie_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        # 移除不兼容的属性
                        cookie.pop('expiry', None)
                        cookie.pop('sameSite', None)

                        # 特别处理 domain 导致报错的问题
                        domain = cookie.get('domain', '')
                        if 'jd.com' in domain:
                            try:
                                self.driver.add_cookie(cookie)
                            except Exception:
                                pass
                return True
            except Exception as e:
                print(f"--> [ERROR] 加载 Cookie 失败: {e}")
        return False

    def save_cookies(self):
        cookies = self.driver.get_cookies()
        with open('jd_cookies.json', 'w', encoding='utf-8') as f:
            json.dump(cookies, f)
        print("--> [INFO] Cookie 已保存")

    def human_like_scroll(self):
        """模拟真人滚动页面"""
        total_height = int(self.driver.execute_script("return document.body.scrollHeight"))
        for i in range(1, total_height, random.randint(200, 400)):
            self.driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(random.uniform(0.1, 0.3))

    def search_jd_real(self, keyword: str, limit: int = 5) -> list:
        print(f"\n=== 开始抓取: {keyword} ===")
        url = f'https://search.jd.com/Search?keyword={quote(keyword)}&enc=utf-8'

        # 1. 访问主页种下基础 Cookie
        self.driver.get('https://www.jd.com')
        time.sleep(2)
        if self.load_cookies():
            self.driver.refresh()
            time.sleep(2)

        # 2. 访问搜索页
        self.driver.get(url)
        time.sleep(5)  # 必须等待，太快会被拦截

        # 3. 检查是否被拦截到安全验证或登录页
        current_url = self.driver.current_url
        if "risk_handler" in current_url or "passport" in current_url:
            print("--> [🛑 触发反爬] 被京东拦截到了安全验证或登录页！")
            print("--> [👉 紧急操作] 请在自动打开的浏览器中，在 60 秒内完成验证或扫码登录！")

            for i in range(60, 0, -1):
                if i % 10 == 0:
                    print(f"    剩余 {i} 秒等待你手动操作...")
                # 检查 URL 是否跳回了正常的搜索页
                if "search.jd.com" in self.driver.current_url:
                    print("--> [✅ 验证/登录通过] 成功返回搜索页！")
                    time.sleep(3)
                    self.save_cookies()
                    break
                time.sleep(1)

        # 再次确保我们在正确的搜索页上
        if "search.jd.com" not in self.driver.current_url:
            print("--> [⚠️ 警告] 依然未能进入搜索页，尝试强制重新加载...")
            self.driver.get(url)
            time.sleep(3)

        # 4. 等待并解析数据
        try:
            print("--> [DEBUG] 正在判断页面是否加载...")
            # 放宽等待条件，等待包含商品的最外层结构
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'J_goodsList'))
            )
            print("--> [DEBUG] 页面主容器已加载。")
        except Exception as e:
            print("--> [WARNING] 未能找到标准商品容器 J_goodsList，但尝试继续提取。")

        # 必须向下滚动触发图片和价格的 AJAX 加载
        print("--> [DEBUG] 正在滚动页面以加载价格信息...")
        self.human_like_scroll()
        time.sleep(2)

        html = self.driver.page_source
        return self._parse_jd_html(html, limit)

    def _parse_jd_html(self, html: str, limit: int) -> list:
        soup = BeautifulSoup(html, 'html.parser')

        # 兼容多种常见的商品列表选择器
        items = soup.select('li.gl-item')
        if not items:
            items = soup.select('#J_goodsList ul li')
        if not items:
            # 有时页面结构是 div.gl-item
            items = soup.select('div.gl-item')

        print(f"--> [DEBUG] 成功解析到 {len(items)} 个商品元素节点。")

        results = []

        for item in items[:limit]:
            try:
                # 1. 提取价格
                price = 0.0
                price_tags = item.select('div.p-price strong i, div.p-price i')
                if price_tags:
                    price_text = price_tags[0].text.replace('￥', '').replace('¥', '').strip()
                    try:
                        price = float(price_text)
                    except ValueError:
                        pass

                # 2. 提取商品名称
                name = '未知商品'
                name_tag = item.select_one('div.p-name em')
                if name_tag:
                    name = name_tag.text.strip()

                # 3. 提取链接
                link = ''
                link_tag = item.select_one('div.p-img a')
                if link_tag and 'href' in link_tag.attrs:
                    link = link_tag['href']
                    if not link.startswith('http'):
                        link = 'https:' + link

                if price > 0:  # 只有成功提取到价格才认为这是一条有效数据
                    results.append({
                        'name': name,
                        'price': price,
                        'link': link,
                        'source': 'jd'
                    })
            except Exception as e:
                print(f"--> [WARNING] 解析单个商品出错: {e}")
                continue

        return results

    def crawl_all(self, app):
        with app.app_context():
            print("=== 开始真实爬取京东数据 ===")
            for keyword in self.CPU_KEYWORDS:
                data_list = self.search_jd_real(keyword, limit=3)
                if not data_list:
                    print(f"--> [WARNING] 未能抓取到关于 {keyword} 的数据！")

                for data in data_list:
                    print(f"✅ 爬取成功: {data['name'][:30]}... | ￥{data['price']}")
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

                # 爬完一个关键词休息一下，防止被封 IP
                time.sleep(random.uniform(3.0, 6.0))

            print("=== 真实爬取完成 ===")

        try:
            self.driver.quit()
        except OSError:
            # 捕获 uc 常见的 [WinError 6] 句柄无效的错误，静默处理
            pass

    def save_item(self, model_class, item_data: dict):
        try:
            item_data.pop('_sa_instance_state', None)
            obj = model_class(**item_data)
            db.session.add(obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
