# -*- coding: utf-8 -*-
"""京东爬虫 - 使用 Selenium 爬取各硬件低价链接"""
import time
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
        # 配置无头浏览器 (Selenium)
        chrome_options = Options()
        # 生产环境/不希望看到浏览器弹窗可以取消注释下面这行：
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        # 伪装User-Agent，防止部分简单的检测
        chrome_options.binary_location = r"I:\ruanjian\Google\Chrome\Application\chrome.exe"

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

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