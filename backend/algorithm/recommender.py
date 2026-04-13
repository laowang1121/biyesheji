# -*- coding: utf-8 -*-
"""配置推荐算法 - 根据预算和场景分配并匹配最优配件"""
import os
import sqlite3
from config import Config
from backend.algorithm.ai_recommender import search_components


class ConfigRecommender:
    """配置推荐器"""
    
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

    def _map_to_table(self, comp: str) -> str:
        mapping = {
            'cpu': 'cpu_analyzed',
            'motherboard': '主板_analyzed',
            'gpu': '显卡_analyzed',
            'memory': '内存条_analyzed',
            'ssd': '固态_analyzed',
            'cooling': '散热_analyzed',
            'case': '机箱_analyzed',
            'psu': '电源_analyzed'
        }
        return mapping.get(comp, f"{comp}_analyzed")

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

        components_list = ['cpu', 'motherboard', 'gpu', 'memory', 'ssd', 'cooling', 'case', 'psu']

        # 初始选择：基础预算内选择最强配置
        for component in components_list:
            budget = self.get_component_budget(component)
            table_name = self._map_to_table(component)

            parts = search_components(table_name, max_price=budget, limit=1, desc=True)
            if not parts:
                # 若无符合的，选最便宜的
                parts = search_components(table_name, limit=1, desc=False)

            if parts:
                item = parts[0]
                components_selected[component] = item
                total_price += float(item.get('价格', item.get('商品价格', 0)))

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
                curr_price = float(current_item.get('价格', current_item.get('商品价格', 0)))
                table_name = self._map_to_table(comp)

                target_max_price = curr_price - (total_price - self.budget)
                if target_max_price <= 0:
                    next_items = search_components(table_name, max_price=curr_price-0.01, limit=1, desc=True)
                else:
                    next_items = search_components(table_name, max_price=target_max_price, limit=1, desc=True)
                    if not next_items:
                        next_items = search_components(table_name, max_price=curr_price-0.01, limit=1, desc=True)

                if next_items:
                    next_price = float(next_items[0].get('价格', next_items[0].get('商品价格', 0)))
                    total_price = total_price - curr_price + next_price
                    components_selected[comp] = next_items[0]
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
                curr_price = float(current_item.get('价格', current_item.get('商品价格', 0)))
                table_name = self._map_to_table(comp)

                remaining_budget = self.budget - total_price
                max_allowed_price = curr_price + remaining_budget

                db_path = os.path.join(Config.BASE_DIR, 'data', 'ai_analyzed.db')
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()

                cur.execute(f"PRAGMA table_info({table_name})")
                cols = [c['name'] for c in cur.fetchall()]
                price_col = '商品价格' if '商品价格' in cols else '价格'

                cur.execute(f"SELECT * FROM {table_name} WHERE CAST({price_col} AS REAL) > ? AND CAST({price_col} AS REAL) <= ? ORDER BY CAST({price_col} AS REAL) DESC LIMIT 1", (curr_price, max_allowed_price))
                row = cur.fetchone()
                conn.close()

                if row:
                    next_item = dict(row)
                    next_price = float(next_item.get('价格', next_item.get('商品价格', 0)))
                    total_price = total_price - curr_price + next_price
                    components_selected[comp] = next_item
                    upgraded = True
                    break

            if not upgraded:
                # 常规升级卡住，强制升级再降级
                for comp in upgrade_priority:
                    if comp not in components_selected: continue
                    current_item = components_selected[comp]
                    curr_price = float(current_item.get('价格', current_item.get('商品价格', 0)))
                    table_name = self._map_to_table(comp)

                    db_path = os.path.join(Config.BASE_DIR, 'data', 'ai_analyzed.db')
                    conn = sqlite3.connect(db_path)
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()

                    cur.execute(f"PRAGMA table_info({table_name})")
                    cols = [c['name'] for c in cur.fetchall()]
                    price_col = '商品价格' if '商品价格' in cols else '价格'

                    cur.execute(f"SELECT * FROM {table_name} WHERE CAST({price_col} AS REAL) > ? ORDER BY CAST({price_col} AS REAL) ASC LIMIT 1", (curr_price,))
                    row = cur.fetchone()
                    conn.close()

                    if row:
                        next_item = dict(row)
                        next_price = float(next_item.get('价格', next_item.get('商品价格', 0)))
                        total_price = total_price - curr_price + next_price
                        components_selected[comp] = next_item
                        upgraded = True

                        # 把超出的价格在次要配件上扣回来
                        for d_comp in downgrade_priority:
                            if total_price <= self.budget: break
                            if d_comp not in components_selected or d_comp == comp: continue
                            d_item = components_selected[d_comp]
                            d_price = float(d_item.get('价格', d_item.get('商品价格', 0)))
                            d_table = self._map_to_table(d_comp)

                            target = d_price - (total_price - self.budget)
                            if target <= 0:
                                lower_items = search_components(d_table, max_price=d_price-0.01, limit=1, desc=True)
                            else:
                                lower_items = search_components(d_table, max_price=target, limit=1, desc=True)
                                if not lower_items:
                                    lower_items = search_components(d_table, max_price=d_price-0.01, limit=1, desc=True)

                            if lower_items:
                                lower_price = float(lower_items[0].get('价格', lower_items[0].get('商品价格', 0)))
                                total_price = total_price - d_price + lower_price
                                components_selected[d_comp] = lower_items[0]
                        break

            if not upgraded:
                break
            iters += 1

        # 确保总价不会因为强制降级而再次超出100%
        if total_price > self.budget:
            for comp in downgrade_priority:
                if total_price <= self.budget: break
                if comp not in components_selected: continue
                current_item = components_selected[comp]
                curr_price = float(current_item.get('价格', current_item.get('商品价格', 0)))
                table_name = self._map_to_table(comp)

                lower_items = search_components(table_name, max_price=curr_price-0.01, limit=1, desc=True)
                if lower_items:
                    lower_price = float(lower_items[0].get('价格', lower_items[0].get('商品价格', 0)))
                    total_price = total_price - curr_price + lower_price
                    components_selected[comp] = lower_items[0]

        # 装配结果
        for component, item in components_selected.items():
            budget = self.get_component_budget(component)
            comp_data = self._model_to_dict(item, component)
            comp_data['allocated_budget'] = budget
            result['components'][component] = comp_data
            result['summary'].append({
                'name': comp_data.get('brand', comp_data.get('model', '未知')),
                'price': comp_data.get('price', 0),
                'link': comp_data.get('link', '')
            })

        result['total_price'] = round(total_price, 2)
        result['budget_usage'] = round(result['total_price'] / self.budget * 100, 1)

        return result

    def _model_to_dict(self, obj: dict, component_type: str) -> dict:
        """将数据字典转换为前端需要的格式"""
        brand = ''
        if component_type == 'cpu' and obj.get('型号'):
            brand = obj.get('型号')
        else:
            brand = obj.get('商品名称', obj.get('商品名字', obj.get('品牌（含具体型号）', obj.get('型号', obj.get('主板型号', obj.get('品牌', '未知配件'))))))

        if component_type == 'memory' and isinstance(brand, str):
            if ' - ' in brand:
                brand = brand.split(' - ')[-1].strip()
            words = brand.split()
            half = len(words) // 2
            if half > 0 and words[:half] == words[half:]:
                brand = ' '.join(words[:half])

        link = obj.get('链接', obj.get('item_url', ''))
        price = float(obj.get('价格', obj.get('商品价格', 0)))

        return {
            'brand': brand,
            'model': brand,  # 兼容前端取 `model || brand`
            'price': price,
            'link': link,
            'raw': obj
        }

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
