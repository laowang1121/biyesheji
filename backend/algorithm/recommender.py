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
        策略：在预算范围内选择价格最接近预算的高性价比产品，并确保总价控制在 90% - 100% 的预算使用率之间
        """
        result = {
            'total_budget': self.budget,
            'mode': self.mode,
            'allocation': self.allocation,
            'components': {},
            'total_price': 0,
            'summary': []
        }
        
        components_selected = {}
        total_price = 0

        # 初始选择：基础预算内选择最强配置
        for component, Model in self.COMPONENT_MAP.items():
            budget = self.get_component_budget(component)
            
            # 初始查询严格控制在预算内
            query = Model.query.filter(Model.price <= budget)
            item = query.order_by(Model.price.desc()).first()
            
            if not item:
                # 若无符合的，选最便宜的
                item = Model.query.order_by(Model.price.asc()).first()
            
            if item:
                components_selected[component] = item
                total_price += item.price

        # 调整逻辑限制预算不超100%，不少于90%
        upgrade_priority = ['gpu', 'cpu', 'ssd', 'memory', 'motherboard', 'cooling', 'case', 'psu']
        downgrade_priority = ['case', 'cooling', 'motherboard', 'memory', 'ssd', 'psu', 'cpu', 'gpu']

        max_iters = 30
        iters = 0

        # 降级：如果超出100%预算
        while total_price > self.budget and iters < max_iters:
            downgraded = False
            for comp in downgrade_priority:
                if comp not in components_selected: continue
                current_item = components_selected[comp]
                Model = self.COMPONENT_MAP[comp]

                target_max_price = current_item.price - (total_price - self.budget)
                if target_max_price <= 0:
                    next_item = Model.query.filter(Model.price < current_item.price).order_by(Model.price.desc()).first()
                else:
                    next_item = Model.query.filter(Model.price <= target_max_price).order_by(Model.price.desc()).first()
                    if not next_item:
                        next_item = Model.query.filter(Model.price < current_item.price).order_by(Model.price.desc()).first()

                if next_item:
                    total_price = total_price - current_item.price + next_item.price
                    components_selected[comp] = next_item
                    downgraded = True
                    break
            if not downgraded:
                break
            iters += 1

        # 升级：如果低于90%预算
        iters = 0
        while total_price < self.budget * 0.9 and iters < max_iters:
            upgraded = False
            for comp in upgrade_priority:
                if comp not in components_selected: continue
                current_item = components_selected[comp]
                Model = self.COMPONENT_MAP[comp]

                remaining_budget = self.budget - total_price
                max_allowed_price = current_item.price + remaining_budget

                # 寻找更贵的但仍在剩余预算内的配件，选最贵的
                next_item = Model.query.filter(Model.price > current_item.price, Model.price <= max_allowed_price).order_by(Model.price.desc()).first()

                if next_item:
                    total_price = total_price - current_item.price + next_item.price
                    components_selected[comp] = next_item
                    upgraded = True
                    break

            if not upgraded:
                # 常规升级卡住，说明任何升级都导致超出预算。采取"强制升级"再降级其它配件策略
                for comp in upgrade_priority:
                    if comp not in components_selected: continue
                    current_item = components_selected[comp]
                    Model = self.COMPONENT_MAP[comp]
                    next_item = Model.query.filter(Model.price > current_item.price).order_by(Model.price.asc()).first()

                    if next_item:
                        total_price = total_price - current_item.price + next_item.price
                        components_selected[comp] = next_item
                        upgraded = True

                        # 把超出的价格在次要配件上扣回来
                        for d_comp in downgrade_priority:
                            if total_price <= self.budget: break
                            if d_comp not in components_selected or d_comp == comp: continue
                            d_item = components_selected[d_comp]
                            d_Model = self.COMPONENT_MAP[d_comp]

                            target = d_item.price - (total_price - self.budget)
                            if target <= 0:
                                lower_item = d_Model.query.filter(d_Model.price < d_item.price).order_by(d_Model.price.desc()).first()
                            else:
                                lower_item = d_Model.query.filter(d_Model.price <= target).order_by(d_Model.price.desc()).first()
                                if not lower_item:
                                    lower_item = d_Model.query.filter(d_Model.price < d_item.price).order_by(d_Model.price.desc()).first()

                            if lower_item:
                                total_price = total_price - d_item.price + lower_item.price
                                components_selected[d_comp] = lower_item
                        break

            if not upgraded:
                break
            iters += 1

        # 确保总价不会因为强制降级而再次超出100%，如果有，再最后粗暴处理一次
        if total_price > self.budget:
            for comp in downgrade_priority:
                if total_price <= self.budget: break
                if comp not in components_selected: continue
                current_item = components_selected[comp]
                Model = self.COMPONENT_MAP[comp]
                lower_item = Model.query.filter(Model.price < current_item.price).order_by(Model.price.desc()).first()
                if lower_item:
                    total_price = total_price - current_item.price + lower_item.price
                    components_selected[comp] = lower_item

        # 装配结果
        for component, item in components_selected.items():
            budget = self.get_component_budget(component)
            comp_data = self._model_to_dict(item, component)
            comp_data['allocated_budget'] = budget
            result['components'][component] = comp_data
            result['summary'].append({
                'name': comp_data.get('model', comp_data.get('model', '')),
                'price': item.price,
                'link': item.link
            })

        result['total_price'] = round(total_price, 2)
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
