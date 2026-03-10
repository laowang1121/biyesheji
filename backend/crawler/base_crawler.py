# -*- coding: utf-8 -*-
"""爬虫基类 - 京东和淘宝有反爬机制，需根据实际情况调整"""
import time
import random
import requests
from fake_useragent import UserAgent
from urllib.parse import quote

ua = UserAgent()


class BaseCrawler:
    """爬虫基类"""
    
    def __init__(self, delay_range=(1, 3)):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self.delay_range = delay_range
    
    def _delay(self):
        """随机延迟，避免被封"""
        time.sleep(random.uniform(*self.delay_range))
    
    def search_jd(self, keyword: str, page: int = 1) -> list:
        """
        京东搜索 - 京东有强反爬，实际需配合Selenium或API
        此处提供框架，返回空列表，可用示例数据填充
        """
        url = f'https://search.jd.com/Search?keyword={quote(keyword)}&enc=utf-8&page={page}'
        try:
            self._delay()
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                # 实际解析需要BeautifulSoup，京东页面结构复杂
                return self._parse_jd_list(resp.text)
        except Exception as e:
            print(f'京东爬取失败 {keyword}: {e}')
        return []
    
    def search_taobao(self, keyword: str, page: int = 1) -> list:
        """
        淘宝搜索 - 使用官方提供的接口
        示例：api.get_product_price(platform="taobao", product_id="123456")
        """
        try:
            # 引入官方 API - 注意替换为您实际的 api 模块或库
            import api  # type: ignore

            results = []
            # 假设您有一个以关键字搜索商品的接口
            # 注意：如果官方 API 只有获取详情和价格，您可能需要提供搜索接口
            # 此处演示如何按照您提供的官方接口查询商品价格和详情：

            # response = api.get_product_price(platform="taobao", product_id="123456")
            # current_price = response['data']['price']
            # details = api.get_product_details(platform="taobao", product_id="123456")

            print(f"调用官方淘宝/拼多多API接口获取数据...")

            return results
        except Exception as e:
            print(f'淘宝API获取失败 {keyword}: {e}')
            return []

    def _parse_jd_list(self, html: str) -> list:
        """解析京东列表页 - 需根据实际页面结构调整"""
        return []
    
    @staticmethod
    def create_sample_data():
        """创建示例数据用于开发测试（京东淘宝反爬严格时的替代方案）
        需在 app.app_context() 内调用"""
        from backend.models import db, CPU, Motherboard, GPU, Memory, SSD, Cooling, Case, PSU
        
        # 检查是否已有数据
        if CPU.query.first():
            print('数据库已有数据，跳过示例数据')
            return
        
        samples = [
            # CPU - 多价位覆盖
            (CPU, [
                {'brand': 'AMD', 'model': '锐龙5 5600', 'series': '锐龙5000', 'package_type': '盒装', 'price': 899, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': 'Intel', 'model': '酷睿i5-12400F', 'series': '酷睿12代', 'package_type': '散片', 'price': 849, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': 'AMD', 'model': '锐龙5 5600G', 'series': '锐龙5000', 'package_type': '盒装', 'price': 699, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': 'AMD', 'model': '锐龙7 7800X3D', 'series': '锐龙7000', 'package_type': '盒装', 'price': 2499, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': 'Intel', 'model': '酷睿i7-13700K', 'series': '酷睿13代', 'package_type': '盒装', 'price': 2299, 'link': 'https://item.jd.com/example', 'source': 'jd'},
            ]),
            # 主板
            (Motherboard, [
                {'brand': '华硕', 'model': 'TUF B550M-PLUS', 'socket': 'AM4', 'price': 699, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '微星', 'model': 'B660M MORTAR', 'socket': 'LGA1700', 'price': 799, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '华擎', 'model': 'B550M Pro4', 'socket': 'AM4', 'price': 499, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '铭瑄', 'model': 'B760M', 'socket': 'LGA1700', 'price': 449, 'link': 'https://item.jd.com/example', 'source': 'jd'},
            ]),
            # 显卡
            (GPU, [
                {'brand': '七彩虹', 'model': 'GTX 1650', 'series': '1600系列', 'chip_brand': 'NVIDIA', 'price': 999, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '华硕', 'model': 'RTX 4060 DUAL', 'series': '4000系列', 'chip_brand': 'NVIDIA', 'price': 2299, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '蓝宝石', 'model': 'RX 7800 XT', 'series': '7000系列', 'chip_brand': 'AMD', 'price': 3499, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '讯景', 'model': 'RX 6600', 'series': '6000系列', 'chip_brand': 'AMD', 'price': 1499, 'link': 'https://item.jd.com/example', 'source': 'jd'},
            ]),
            # 内存
            (Memory, [
                {'brand': '金士顿', 'model': 'DDR4 3200 16G', 'type': 'DDR4', 'capacity': '16G', 'price': 199, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '威刚', 'model': 'DDR5 5600 16G', 'type': 'DDR5', 'capacity': '16G', 'price': 299, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '金百达', 'model': 'DDR4 3200 8G', 'type': 'DDR4', 'capacity': '8G', 'price': 99, 'link': 'https://item.jd.com/example', 'source': 'jd'},
            ]),
            # 固态
            (SSD, [
                {'brand': '三星', 'model': '980 500G', 'interface': 'PCIe3.0', 'capacity': '500G', 'price': 299, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '西数', 'model': 'SN770 1T', 'interface': 'PCIe4.0', 'capacity': '1T', 'price': 449, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '致钛', 'model': 'TiPlus5000 512G', 'interface': 'PCIe3.0', 'capacity': '500G', 'price': 249, 'link': 'https://item.jd.com/example', 'source': 'jd'},
            ]),
            # 散热
            (Cooling, [
                {'brand': '利民', 'model': 'AX120 R SE', 'type': '风冷', 'price': 69, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '九州风神', 'model': 'LS720 360', 'type': '水冷360', 'price': 399, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '乔思伯', 'model': 'CR1400', 'type': '风冷', 'price': 49, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '酷冷至尊', 'model': '冰神240', 'type': '水冷240', 'price': 299, 'link': 'https://item.jd.com/example', 'source': 'jd'},
            ]),
            # 机箱
            (Case, [
                {'brand': '先马', 'model': '平头哥M1', 'style': '普通', 'price': 89, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '联力', 'model': '包豪斯O11', 'style': '海景房', 'price': 499, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '爱国者', 'model': 'YOGO M2', 'style': '普通', 'price': 199, 'link': 'https://item.jd.com/example', 'source': 'jd'},
            ]),
            # 电源
            (PSU, [
                {'brand': '海韵', 'model': 'FOCUS 450W', 'wattage': '450W', 'certification': '金牌', 'price': 299, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '海韵', 'model': 'FOCUS 550W', 'wattage': '550W', 'certification': '金牌全模组', 'price': 399, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '振华', 'model': 'LEADEX 650W', 'wattage': '650W', 'certification': '金牌全模组', 'price': 499, 'link': 'https://item.jd.com/example', 'source': 'jd'},
                {'brand': '振华', 'model': 'LEADEX 750W', 'wattage': '750W', 'certification': '金牌全模组', 'price': 599, 'link': 'https://item.jd.com/example', 'source': 'jd'},
            ]),
        ]
        
        for Model, items in samples:
            for item in items:
                obj = Model(**item)
                db.session.add(obj)
        db.session.commit()
        print('示例数据创建完成')
