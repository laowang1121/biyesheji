# -*- coding: utf-8 -*-
"""京东爬虫 - 使用 undetected_chromedriver 绕过反爬"""
import time
import os
import sys
import json
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote

# 导入 undetected_chromedriver
import undetected_chromedriver as uc

from backend.crawler.base_crawler import BaseCrawler
from backend.models import db, CPU  # 这里先以CPU为例测试，您可以引入其他硬件模型


class JDCrawler():
    """京东硬件真实爬虫"""

    CPU_KEYWORDS = ['AMD 锐龙5', 'Intel 酷睿 i5']

    def __init__(self):
        super().__init__()
        print("--> [DEBUG] JDCrawler 初始化开始")

        # 配置 undetected_chromedriver 的 Options
        options = uc.ChromeOptions()
        # 生产环境/不希望看到浏览器弹窗可以取消注释下面这行：
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # 禁用图片加载可以加快速度并减少被检测概率，但如果您需要截图排查请先注释掉
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # options.add_experimental_option("prefs", prefs)

        # 尝试寻找本地 chrome 安装路径 (undetected_chromedriver 通常能自己找到，找不到时才需要)
        # 您可以根据实际情况保留或删除这段寻找逻辑
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
                options.binary_location = path
                found_binary = True
                break

        if not found_binary:
            print("--> [WARNING] 未能在常见路径找到 chrome.exe，undetected_chromedriver 将尝试自行寻找...")

        driver_path = r"I:\pycharm\PycharmProjects\biyesheji\chromedriver.exe"
        if not os.path.exists(driver_path):
            print(f"--> [ERROR] 找不到驱动文件！请确保已将 chromedriver.exe 放在: {driver_path}")
            raise FileNotFoundError(f"找不到驱动文件: {driver_path}")

        print(f"--> [DEBUG] 成功找到本地驱动: {driver_path}")
        print("--> [DEBUG] 正在启动 undetected_chromedriver ...")

        try:
            # 关键修改：使用 uc.Chrome 初始化，并传入 driver_executable_path
            self.driver = uc.Chrome(options=options, driver_executable_path=driver_path)
            print("--> [DEBUG] 浏览器启动成功！")

            # 设置隐式等待，作为显式等待的补充
            self.driver.implicitly_wait(5)

        except Exception as e:
            print("\n" + "=" * 50)
            print("❌ undetected_chromedriver 启动失败！")
            print(f"报错信息:\n{e}")
            print("=" * 50 + "\n")
            raise e

    def load_cookies(self):
        """加载本地 Cookie"""
        cookie_path = 'jd_cookies.json'
        if os.path.exists(cookie_path):
            with open(cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                for cookie in cookies:
                    # 过滤掉一些可能引起问题的字段
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        print(f"添加 Cookie 失败: {e}, cookie: {cookie}")
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
        print("--> [DEBUG] 正在访问京东主页植入 Cookie...")
        self.driver.get('https://www.jd.com')

        # 尝试加载 cookie 并刷新
        if self.load_cookies():
            print("--> [DEBUG] 刷新页面使 Cookie 生效...")
            self.driver.refresh()
            time.sleep(2)  # 给页面一点加载时间

        print(f"--> [DEBUG] 准备跳转到搜索页: {url}")
        self.driver.get(url)

        # 检查是否成功进入了搜索结果页，还是被拦截重定向了
        current_url = self.driver.current_url
        print(f"--> [DEBUG] 当前停留的 URL: {current_url}")

        # 登录检测逻辑
        if "passport" in current_url or "login" in current_url:
            print("--> [🛑 触发反爬] 京东要求登录或 Cookie 已失效！")
            print("--> [👉 操作提示] 请在弹出的浏览器窗口中，60秒内使用京东APP【扫码登录】...")

            # 给用户 60 秒时间手动扫码
            for i in range(60, 0, -1):
                if i % 10 == 0:
                    print(f"    剩余 {i} 秒...")
                if "passport" not in self.driver.current_url and "login" not in self.driver.current_url:
                    print("--> [✅ 状态] 检测到网址变化，登录成功！")
                    # 登录成功后，稍等一下再保存 cookie，确保完全写入
                    time.sleep(3)
                    self.save_cookies()
                    break
                time.sleep(1)

            if "passport" in self.driver.current_url or "login" in self.driver.current_url:
                print("--> [⚠️ 超时] 似乎未完成登录，继续执行可能无法获取数据...")
            else:
                print("--> [DEBUG] 重新进入搜索页...")
                self.driver.get(url)

        # ---------------- 核心排查修改点 ----------------
        # 等待商品列表加载出来，时间延长到 15 秒
        try:
            print("--> [DEBUG] 正在等待商品列表加载 (gl-item)...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'gl-item'))
            )
            print("--> [DEBUG] 商品列表加载成功！")
        except Exception as e:
            print(f"--> [ERROR] 等待商品列表加载失败！")

            # 保存失败时的现场证据（截图和 HTML）
            timestamp = int(time.time())
            error_img = f"error_screenshot_{timestamp}.png"
            error_html = f"error_page_{timestamp}.html"

            try:
                self.driver.save_screenshot(error_img)
                with open(error_html, "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print(f"--> 📸 已将出错页面截图保存为: {error_img}")
                print(f"--> 📄 已将出错页面源码保存为: {error_html}")
                print("--> 【排查建议】：请去项目文件夹里打开那张 PNG 图片，看看京东当时是不是弹出了验证码或需要登录！")
            except Exception as e2:
                print(f"--> 保存错误现场失败: {e2}")

            return []
        # ------------------------------------------------

        # 稍微往下滚动，触发图片和价格动态加载
        print("--> [DEBUG] 滚动页面以加载动态内容...")
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

            # 为了确保有时间看到最后的页面状态，可以稍微停顿一下
            # time.sleep(5)
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
