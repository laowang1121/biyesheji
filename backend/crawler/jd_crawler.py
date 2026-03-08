# -*- coding: utf-8 -*-
"""京东爬虫 - 爬取各硬件低价链接
注意：京东有反爬机制，生产环境可能需要Selenium或代理池"""
from backend.crawler.base_crawler import BaseCrawler
from backend.models import db, CPU, Motherboard, GPU, Memory, SSD, Cooling, Case, PSU


class JDCrawler(BaseCrawler):
    """京东硬件爬虫"""
    
    # 搜索关键词配置
    CPU_KEYWORDS = [
        'AMD 锐龙', 'Intel 酷睿', '锐龙5', '锐龙7', '锐龙9',
        'i5 散片', 'i7 散片', 'i5 盒装', 'i7 盒装'
    ]
    MB_KEYWORDS = ['华硕主板', '微星主板', '华擎主板', '铭瑄主板']
    GPU_KEYWORDS = [
        'AMD RX 6000', 'AMD RX 7000', 'AMD RX 9000',
        'RTX 4060', 'RTX 4070', 'RTX 4080', 'RTX 4090',
        'RTX 5060', 'RTX 5070', 'Intel 显卡 B500'
    ]
    
    def crawl_all(self, app):
        """执行全量爬取并入库"""
        with app.app_context():
            # 实际爬取逻辑 - 京东需处理反爬
            # 这里提供框架，可替换为Selenium或API
            pass
    
    def save_item(self, model_class, item_data: dict):
        """保存单条数据"""
        obj = model_class(**item_data)
        db.session.add(obj)
        db.session.commit()
