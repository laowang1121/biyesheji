# -*- coding: utf-8 -*-
"""配置推荐算法 - 根据预算和场景分配并匹配最优配件"""
from backend.models import (
    db, CPU, Motherboard, GPU, Memory, SSD, Cooling, Case, PSU
)
from config import Config


class ConfigRecommender:
    """配置推荐器"""
    
    # 配件类型与模型映射
    COMPONENT_MAP = {
        'cpu': CPU,
        'motherboard': Motherboard,
        'gpu': GPU,
        'memory': Memory,
        'ssd': SSD,
        'cooling': Cooling,
        'case': Case,
        'psu': PSU,
    }
    
    # 默认预算分配（取区间中值）
    DEFAULT_OFFICE = {
        'cpu': 22.5, 'gpu': 22.5, 'motherboard': 12.5, 'memory': 15,
        'ssd': 11.5, 'psu': 6.5, 'cooling': 4, 'case': 4
    }
    
    DEFAULT_GAMING = {
        'cpu': 12.5, 'gpu': 35, 'motherboard': 7.5, 'memory': 15,
        'ssd': 7.5, 'psu': 6.5, 'cooling': 4, 'case': 4
    }
    
    def __init__(self, budget: float, mode: str = 'office', custom_allocation: dict = None):
        """
        Args:
            budget: 总预算（元）
            mode: 模式 - office(办公), gaming(游戏), custom(自定义)
            custom_allocation: 自定义分配比例，如 {'cpu': 20, 'gpu': 30, ...}
        """
        self.budget = budget
        self.mode = mode
        
        if mode == 'custom' and custom_allocation:
            total = sum(custom_allocation.values())
            if total > 100:
                raise ValueError('自定义分配总和不能超过100%')
            self.allocation = custom_allocation
        elif mode == 'gaming':
            self.allocation = self.DEFAULT_GAMING.copy()
        else:
            self.allocation = self.DEFAULT_OFFICE.copy()
    
    def get_component_budget(self, component: str) -> float:
        """获取某配件的预算"""
        ratio = self.allocation.get(component, 0) / 100
        return round(self.budget * ratio, 2)
    
    def recommend(self) -> dict:
        """
        执行推荐，返回各配件的最优选择
        策略：在预算范围内选择价格最接近预算的高性价比产品
        """
        result = {
            'total_budget': self.budget,
            'mode': self.mode,
            'allocation': self.allocation,
            'components': {},
            'total_price': 0,
            'summary': []
        }
        
        for component, Model in self.COMPONENT_MAP.items():
            budget = self.get_component_budget(component)
            
            # 查询该配件，按价格排序，选择预算内最贵的（通常性能更好）
            query = Model.query.filter(Model.price <= budget * 1.1)  # 允许10%溢出
            item = query.order_by(Model.price.desc()).first()
            
            if not item:
                # 若无符合的，选最便宜的
                item = Model.query.order_by(Model.price.asc()).first()
            
            if item:
                comp_data = self._model_to_dict(item, component)
                comp_data['allocated_budget'] = budget
                result['components'][component] = comp_data
                result['total_price'] += item.price
                result['summary'].append({
                    'name': comp_data.get('model', comp_data.get('model', '')),
                    'price': item.price,
                    'link': item.link
                })
        
        result['total_price'] = round(result['total_price'], 2)
        result['budget_usage'] = round(result['total_price'] / self.budget * 100, 1)
        
        return result
    
    def _model_to_dict(self, obj, component_type: str) -> dict:
        """将模型对象转为字典"""
        d = {
            'id': obj.id,
            'brand': obj.brand,
            'model': obj.model,
            'price': obj.price,
            'link': obj.link,
            'source': obj.source,
        }
        # 添加类型特定字段
        if hasattr(obj, 'series'):
            d['series'] = obj.series
        if hasattr(obj, 'type'):
            d['type'] = obj.type
        if hasattr(obj, 'capacity'):
            d['capacity'] = obj.capacity
        if hasattr(obj, 'wattage'):
            d['wattage'] = obj.wattage
        return d
    
    @staticmethod
    def validate_custom_allocation(allocation: dict):
        """
        验证自定义分配
        Returns: (bool, str) 是否有效, 错误信息
        """
        required = ['cpu', 'gpu', 'motherboard', 'memory', 'ssd', 'psu', 'cooling', 'case']
        for k in required:
            if k not in allocation:
                return False, f'缺少配件分配: {k}'
        
        total = sum(allocation.values())
        if total > 100:
            return False, f'分配总和不能超过100%，当前为{total}%'
        
        for k, v in allocation.items():
            if v < 0:
                return False, f'{k} 的比例不能为负数'
        
        return True, ''
