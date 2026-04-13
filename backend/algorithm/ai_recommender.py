# -*- coding: utf-8 -*-
"""AI智能推荐服务 - 根据需求自然语言调用数据库"""
import os
import json
import sqlite3
from config import Config
from openai import OpenAI
import re

def get_db_connection():
    db_path = os.path.join(Config.BASE_DIR, 'data', 'ai_analyzed.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def search_components(table_name, max_price=None, min_price=None, keyword=None, limit=5, desc=True, generation=None, cpu_brand=None):
    """从本地分析库搜索配件"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"PRAGMA table_info({table_name})")
    cols = [c['name'] for c in cur.fetchall()]
    price_col = '商品价格' if '商品价格' in cols else '价格'

    query = f"SELECT * FROM {table_name} WHERE 1=1"
    params = []

    if max_price:
        query += f" AND CAST({price_col} AS REAL) <= ?"
        params.append(max_price)
    if min_price:
        query += f" AND CAST({price_col} AS REAL) >= ?"
        params.append(min_price)

    if generation and table_name == '内存条_analyzed':
        if '代数' in cols:
            query += " AND 代数 = ?"
            params.append(generation)
        else:
            query += f" AND (商品名称 LIKE ? OR 容量 LIKE ? OR 频率 LIKE ?)"
            params.extend([f"%{generation}%", f"%{generation}%", f"%{generation}%"])

    if generation and table_name == '主板_analyzed':
        if generation == 'DDR4':
            query += " AND (商品名字 LIKE '%D4%' OR 商品名字 LIKE '%DDR4%')"
        elif generation == 'DDR5':
            query += " AND (商品名字 LIKE '%D5%' OR 商品名字 LIKE '%DDR5%' OR (商品名字 NOT LIKE '%D4%' AND 商品名字 NOT LIKE '%DDR4%'))"

    if cpu_brand and table_name == '主板_analyzed':
        if cpu_brand == 'AMD':
            query += " AND (商品名字 LIKE '%B650%' OR 商品名字 LIKE '%B850%')"
        elif cpu_brand == 'Intel':
            query += " AND (商品名字 NOT LIKE '%B650%' AND 商品名字 NOT LIKE '%B850%')"

    if cpu_brand and table_name == 'cpu_analyzed':
        if cpu_brand == 'AMD':
            query += " AND (型号 LIKE '%R%' OR 商品名字 LIKE '%AMD%' OR 商品名字 LIKE '%锐龙%')"
        elif cpu_brand == 'Intel':
            query += " AND (型号 NOT LIKE '%R%' AND 商品名字 NOT LIKE '%AMD%' AND 商品名字 NOT LIKE '%锐龙%')"

    order = "DESC" if desc else "ASC"
    query += f" ORDER BY CAST({price_col} AS REAL) {order} LIMIT ?"
    params.append(limit)

    try:
        cur.execute(query, tuple(params))
        rows = [dict(ix) for ix in cur.fetchall()]
        return rows
    except Exception as e:
        return []
    finally:
        conn.close()

def generate_ai_recommend(prompt: str):
    import random
    from openai import OpenAI

    # 1. 尝试通过AI或正则获取预算
    budget_match = re.search(r'(\d+)\s*[元块wWw]', prompt)
    if budget_match:
        val = budget_match.group(1)
        # 简单兼容处理比如 5w -> 50000
        budget = int(val) * 10000 if 'w' in prompt.lower() and len(val)<3 else int(val)
    else:
        budget = 5000

    # 2. 识别品牌倾向
    forced_brand = None
    if 'AMD' in prompt.upper() or '锐龙' in prompt or 'B650' in prompt.upper() or 'B850' in prompt.upper():
        forced_brand = 'AMD'
    elif 'INTEL' in prompt.upper() or '英特尔' in prompt or 'B760' in prompt.upper() or 'Z790' in prompt.upper() or '酷睿' in prompt:
        forced_brand = 'Intel'

    # 模式分配（粗略）
    if '游戏' in prompt or '电竞' in prompt:
        allocation = {
            'cpu_analyzed': 0.15, '显卡_analyzed': 0.45, '主板_analyzed': 0.10,
            '内存条_analyzed': 0.05, '固态_analyzed': 0.10, '电源_analyzed': 0.05,
            '散热_analyzed': 0.05, '机箱_analyzed': 0.05
        }
    else:
        allocation = {
            'cpu_analyzed': 0.30, '显卡_analyzed': 0.15, '主板_analyzed': 0.15,
            '内存条_analyzed': 0.10, '固态_analyzed': 0.10, '电源_analyzed': 0.08,
            '散热_analyzed': 0.07, '机箱_analyzed': 0.05
        }

    components_selected = {}
    total_price = 0
    result = {'total_budget': budget, 'components': {}, 'ai_message': f"根据需求 '{prompt}'，正在调用 ai_analyzed.db 数据库："}
    mb_generation = None
    cpu_brand = forced_brand

    # 第一优先级选主板，以确定代数
    ordered_tables = ['cpu_analyzed', '主板_analyzed', '显卡_analyzed', '内存条_analyzed', '固态_analyzed', '电源_analyzed', '散热_analyzed', '机箱_analyzed']

    # 初始选择：预算以内最强的配件
    for table in ordered_tables:
        if table not in allocation: continue
        ratio = allocation[table]
        part_budget = budget * ratio

        kwargs = {'max_price': part_budget, 'limit': 1, 'desc': True}
        if mb_generation:
            if table == '内存条_analyzed':
                kwargs['generation'] = mb_generation
            elif table == '主板_analyzed':
                kwargs['generation'] = mb_generation

        if cpu_brand and table in ['主板_analyzed', 'cpu_analyzed']:
            kwargs['cpu_brand'] = cpu_brand

        parts = search_components(table, **kwargs)
        if not parts:
            kwargs['desc'] = False
            kwargs.pop('max_price', None)
            parts = search_components(table, **kwargs)

        if parts:
            part = parts[0]
            components_selected[table] = part
            total_price += float(part.get('价格', part.get('商品价格', 0)))

            if table == 'cpu_analyzed' and not cpu_brand:
                cpu_name = str(part.get('型号', '')) + ' ' + str(part.get('商品名字', ''))
                cpu_name = cpu_name.upper()
                if 'R3' in cpu_name or 'R5' in cpu_name or 'R7' in cpu_name or 'R9' in cpu_name or 'AMD' in cpu_name or '锐龙' in cpu_name:
                    cpu_brand = 'AMD'
                else:
                    cpu_brand = 'Intel'

            if table == '主板_analyzed':
                mb_name = part.get('商品名字', '').upper()
                if 'D4' in mb_name or 'DDR4' in mb_name:
                    mb_generation = 'DDR4'
                else:
                    mb_generation = 'DDR5'

    # ========= 预算控制逻辑 90% - 100% =========
    upgrade_priority = ['显卡_analyzed', 'cpu_analyzed', '固态_analyzed', '内存条_analyzed', '主板_analyzed', '电源_analyzed', '散热_analyzed', '机箱_analyzed']
    downgrade_priority = ['机箱_analyzed', '散热_analyzed', '电源_analyzed', '固态_analyzed', '主板_analyzed', '内存条_analyzed', 'cpu_analyzed', '显卡_analyzed']

    max_iters = 30
    iters = 0

    # 超出100%则降级
    while total_price > budget and iters < max_iters:
        downgraded = False
        for comp in downgrade_priority:
            if comp not in components_selected: continue
            curr_item = components_selected[comp]
            curr_price = float(curr_item.get('价格', 0))

            target_max = curr_price - (total_price - budget)

            kwargs_down = {'limit': 1, 'desc': True}
            if comp == '内存条_analyzed' and mb_generation:
                kwargs_down['generation'] = mb_generation
            elif comp == '主板_analyzed' and mb_generation:
                kwargs_down['generation'] = mb_generation

            if cpu_brand and comp in ['主板_analyzed', 'cpu_analyzed']:
                kwargs_down['cpu_brand'] = cpu_brand

            if target_max <= 0:
                kwargs_down['max_price'] = curr_price - 0.01
                next_items = search_components(comp, **kwargs_down)
            else:
                kwargs_down['max_price'] = target_max
                next_items = search_components(comp, **kwargs_down)
                if not next_items:
                    kwargs_down['max_price'] = curr_price - 0.01
                    next_items = search_components(comp, **kwargs_down)

            if next_items:
                components_selected[comp] = next_items[0]
                total_price = total_price - curr_price + float(next_items[0].get('价格', next_items[0].get('商品价格', 0)))
                downgraded = True
                break
        if not downgraded: break
        iters+=1

    # 低于90%则升级
    iters = 0
    while total_price < budget * 0.9 and iters < max_iters:
        upgraded = False
        for comp in upgrade_priority:
            if comp not in components_selected: continue
            curr_item = components_selected[comp]
            curr_price = float(curr_item.get('价格', 0))

            remaining = budget - total_price
            max_allowed = curr_price + remaining

            # 寻找当前价格之上但未超剩下的最多预算的最强配件
            # 因为我们的search是 <= max_price, 我们只需要找 <= max_allowed 且满足 > curr_price 即可
            # 简单实现：我们查 <= max_allowed 且比当前价格大的。
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(f"PRAGMA table_info({comp})")
            cols = [c['name'] for c in cur.fetchall()]
            price_col = '商品价格' if '商品价格' in cols else '价格'

            q_cond = ""
            q_params = []
            if comp == '内存条_analyzed' and mb_generation:
                if '代数' in cols:
                    q_cond = " AND 代数 = ?"
                    q_params.append(mb_generation)
            elif comp == '主板_analyzed' and mb_generation:
                if mb_generation == 'DDR4':
                    q_cond = " AND (商品名字 LIKE '%D4%' OR 商品名字 LIKE '%DDR4%')"
                else:
                    q_cond = " AND (商品名字 NOT LIKE '%D4%' AND 商品名字 NOT LIKE '%DDR4%')"

            if comp == '主板_analyzed' and cpu_brand:
                if cpu_brand == 'AMD':
                    q_cond += " AND (商品名字 LIKE '%B650%' OR 商品名字 LIKE '%B850%')"
                elif cpu_brand == 'Intel':
                    q_cond += " AND (商品名字 NOT LIKE '%B650%' AND 商品名字 NOT LIKE '%B850%')"
            elif comp == 'cpu_analyzed' and cpu_brand:
                if cpu_brand == 'AMD':
                    q_cond += " AND (型号 LIKE '%R%' OR 商品名字 LIKE '%AMD%' OR 商品名字 LIKE '%锐龙%')"
                elif cpu_brand == 'Intel':
                    q_cond += " AND (型号 NOT LIKE '%R%' AND 商品名字 NOT LIKE '%AMD%' AND 商品名字 NOT LIKE '%锐龙%')"

            cur.execute(f"SELECT * FROM {comp} WHERE CAST({price_col} AS REAL) > ? AND CAST({price_col} AS REAL) <= ? {q_cond} ORDER BY CAST({price_col} AS REAL) DESC LIMIT 1", (curr_price, max_allowed) + tuple(q_params))
            row = cur.fetchone()
            conn.close()

            if row:
                next_item = dict(row)
                components_selected[comp] = next_item
                total_price = total_price - curr_price + float(next_item.get('价格', next_item.get('商品价格', 0)))
                upgraded = True
                break

        if not upgraded: break
        iters+=1

    for table, part in components_selected.items():
        price = float(part.get('价格', part.get('商品价格', 0)))
        # 提取字段以便前端展示兼容老版或直接展示
        # 根据ai_analyzed.db结构提取
        brand_str = ''
        if table == 'cpu_analyzed' and part.get('型号'):
            brand_str = part.get('型号')
        else:
            brand_str = part.get('商品名称', part.get('商品名字', part.get('品牌（含具体型号）', part.get('型号', part.get('主板型号', part.get('品牌', '未知配件'))))))

        if table == '内存条_analyzed' and isinstance(brand_str, str):
            if ' - ' in brand_str:
                brand_str = brand_str.split(' - ')[-1].strip()
            words = brand_str.split()
            half = len(words) // 2
            if half > 0 and words[:half] == words[half:]:
                brand_str = ' '.join(words[:half])

        display_part = {
            'brand': brand_str,
            'link': part.get('链接', part.get('item_url', '')),
            'price': price,
            'raw': part
        }

        # 归一化table名称为老定义的key (或保留原名)
        key_map = {
            'cpu_analyzed': 'cpu',
            '主板_analyzed': 'motherboard',
            '显卡_analyzed': 'gpu',
            '内存条_analyzed': 'memory',
            '固态_analyzed': 'ssd',
            '散热_analyzed': 'cooling',
            '机箱_analyzed': 'case',
            '电源_analyzed': 'psu'
        }
        real_key = key_map.get(table, table)
        result['components'][real_key] = display_part

    result['total_price'] = round(total_price, 2)
    result['budget_usage'] = round((total_price / budget) * 100, 2)
    return result

