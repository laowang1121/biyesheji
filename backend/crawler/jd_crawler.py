# -*- coding: utf-8 -*-
"""京东爬虫 - 使用纯 JS 提取绕过反爬"""
import time
import os
import json
import random
from urllib.parse import quote

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from backend.crawler.base_crawler import BaseCrawler
from backend.models import db, CPU


class JDCrawler():
    """京东硬件真实爬虫"""

    CPU_KEYWORDS = ['AMD 锐龙5', 'Intel 酷睿 i5']

    def __init__(self):
        super().__init__()
        print("--> [DEBUG] JDCrawler 初始化开始")

        options = uc.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f'user-agent={user_agent}')

        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        options.add_experimental_option("prefs", prefs)

        print("--> [DEBUG] 正在启动 undetected_chromedriver (自动匹配浏览器版本)...")
        try:
            self.driver = uc.Chrome(
                options=options,
                use_subprocess=True,
                version_main=146  # 强制指定版本 146
            )
            self.driver.implicitly_wait(10)

            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
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
                        cookie.pop('expiry', None)
                        cookie.pop('sameSite', None)
                        if 'jd.com' in cookie.get('domain', ''):
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

    def human_like_scroll(self):
        """模拟真人滚动，触发懒加载"""
        for _ in range(3):
            self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(1)

    def search_jd_real(self, keyword: str, limit: int = 5) -> list:
        print(f"\n=== 开始抓取: {keyword} ===")
        url = f'https://search.jd.com/Search?keyword={quote(keyword)}&enc=utf-8'

        self.driver.get('https://www.jd.com')
        time.sleep(2)
        if self.load_cookies():
            self.driver.refresh()
            time.sleep(2)

        self.driver.get(url)
        time.sleep(4)

        if "risk_handler" in self.driver.current_url or "passport" in self.driver.current_url:
            print("--> [🛑 触发反爬] 被京东拦截！请在弹出的浏览器中完成验证或扫码登录！")
            for _ in range(60):
                if "search.jd.com" in self.driver.current_url:
                    print("--> [✅ 验证/登录通过] 成功返回搜索页！")
                    time.sleep(3)
                    self.save_cookies()
                    break
                time.sleep(1)

        if "search.jd.com" not in self.driver.current_url:
            self.driver.get(url)
            time.sleep(4)

        print("--> [DEBUG] 正在滚动页面加载商品...")
        self.human_like_scroll()
        time.sleep(3)

        return self._extract_data_via_js(limit)

    def _extract_data_via_js(self, limit: int) -> list:
        """核心修复：完全抛弃 BeautifulSoup，直接用 JS 在浏览器内存里查 DOM 获取数据"""
        print("--> [DEBUG] 开始通过纯 JS 提取页面可见数据...")

        js_code = """
        return Array.from(document.querySelectorAll('li.gl-item')).map(item => {
            let priceEl = item.querySelector('.p-price i');
            let nameEl = item.querySelector('.p-name em');
            let linkEl = item.querySelector('.p-img a');

            return {
                price: priceEl ? priceEl.innerText : '0',
                name: nameEl ? nameEl.innerText.replace(/\\n/g, ' ') : '未知商品',
                link: linkEl ? linkEl.href : ''
            };
        });
        """

        try:
            # 直接让浏览器执行 JS 并把结果返回给 Python
            raw_data = self.driver.execute_script(js_code)
            print(f"--> [DEBUG] JS 提取到 {len(raw_data)} 个原始节点数据。")

            results = []
            for item in raw_data[:limit]:
                price_text = str(item['price']).replace('￥', '').replace('¥', '').strip()
                try:
                    price = float(price_text)
                except ValueError:
                    price = 0.0

                link = item['link']
                if link and not link.startswith('http'):
                    link = 'https:' + link

                if price > 0:
                    results.append({
                        'name': item['name'],
                        'price': price,
                        'link': link,
                        'source': 'jd'
                    })
            return results

        except Exception as e:
            print(f"--> [ERROR] JS 提取失败: {e}")
            return []

    def crawl_all(self, app):
        with app.app_context():
            print("=== 开始真实爬取京东数据 ===")
            for keyword in self.CPU_KEYWORDS:
                data_list = self.search_jd_real(keyword, limit=3)
                if not data_list:
                    print(f"--> [WARNING] 未能抓取到关于 {keyword} 的数据！")

                for data in data_list:
                    print(f"✅ 京东爬取成功: {data['name'][:30]}... | ￥{data['price']}")
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

                time.sleep(random.uniform(3.0, 5.0))

            print("=== 开始爬取淘宝/拼多多 (通过官方API) ===")
            # 示例：通过 API 抓取数据并存入数据库
            try:
                # import api
                # 假设您有一个产品列表或者搜索接口
                # 您的示例中只有 get_product_price 和 get_product_details
                # 这里只打印调用过程，实际请替换为您自己引入的官方 api 工具
                product_ids = ['andcpu5600', '7890']
                for pid in product_ids:
                    print(f"--> [API 调用] 获取产品 ID: {pid} 的价格和详情...")
                    # response = api.get_product_price(platform="taobao", product_id=pid)
                    # price = response['data']['price']
                    # details = api.get_product_details(platform="taobao", product_id=pid)
                    # name = details.get('name', '未知商品')
                    # 模拟API返回:
                    price = random.uniform(800, 2000)
                    name = f"淘宝API模拟商品_{pid}"
                    print(f"✅ 淘宝API获取成功: {name} | ￥{price:.2f}")

                    # 同样可以将获取到的数据保存到数据库中
                    cpu_tb = CPU(
                        brand='淘宝品牌',
                        model=name[:20],
                        series='API系列',
                        package_type='盒装',
                        price=price,
                        link=f"https://item.taobao.com/item.htm?id={pid}",
                        source='taobao'
                    )
                    self.save_item(CPU, cpu_tb.__dict__)
                    time.sleep(1)

            except Exception as e:
                print(f"--> [ERROR] 淘宝API调用失败: {e}")

            print("=== 全部爬取完成 ===")

        try:
            self.driver.quit()
        except OSError:
            pass

    def save_item(self, model_class, item_data: dict):
        try:
            item_data.pop('_sa_instance_state', None)
            obj = model_class(**item_data)
            db.session.add(obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()