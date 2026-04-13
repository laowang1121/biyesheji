import urllib.parse
import os
import random
import time
from DrissionPage import ChromiumPage, ChromiumOptions
from db import init_db, get_table_name


def scrape_and_save(keyword):
    user_data_dir = os.path.join(os.getcwd(), "taobao_debug_data")

    print("======================================================")
    print("⚠️  防封号终极模式：使用 DrissionPage 接管浏览器")
    print("======================================================")

    co = ChromiumOptions()
    co.set_local_port(9222)
    co.set_user_data_path(user_data_dir)
    co.set_argument('--disable-blink-features=AutomationControlled')

    try:
        page = ChromiumPage(addr_or_opts=co)
    except Exception as e:
        print(f"❌ 浏览器启动失败: {e}")
        return

    # 核心改变：直接去访问淘宝
    print("准备进入淘宝首页...")
    try:
        page.get("https://www.taobao.com", timeout=60)
        page.wait(3)
    except Exception as e:
        print(f"\n❌ 网络连接失败: {e}")
        page.quit()
        return

    print("==================================================")
    print("如果页面正常显示，请使用手机淘宝扫码登录！")
    print("==================================================")
    input("【等待操作】扫码登录成功，且页面跳转后，请在此按回车键继续搜索...")

    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://s.taobao.com/search?q={encoded_keyword}"

    print(f"正在前往搜索页: {url}")

    try:
        page.get(url)
        page.wait(3)
    except Exception as e:
        print(f"搜索页加载出错: {e}")

    # 等待商品出现
    try:
        page.wait.ele_loaded('xpath://*[@data-spm-act-id]', timeout=15)
    except:
        input("若遇到滑块验证，请手动滑过，出现商品后按回车继续...")

    # 提取商品
    elements = page.eles('xpath://*[@data-spm-act-id]')
    item_ids = []
    for el in elements:
        act_id = el.attr('data-spm-act-id')
        if act_id and act_id not in item_ids:
            item_ids.append(act_id)
        if len(item_ids) >= 3:
            break

    if item_ids:
        conn = init_db()
        cursor = conn.cursor()
        table_name = get_table_name(keyword)
        platform_name = "淘宝"

        for index, iid in enumerate(item_ids):
            item_url = f"https://item.taobao.com/item.htm?id={iid}"
            print(f"[{index + 1}/{len(item_ids)}] 获取: {item_url}")

            try:
                page.get(item_url)
                page.wait(3)

                if index == 0:
                    input("【首次验证】如果出现滑块，请滑动。正常显示后按回车继续...")

                page_title = page.title
                if "验证" in page_title or "滑动" in page_title: continue

                if page.eles('@data-disabled=true') and not page.eles('.content--DIGuLqdf'):
                    continue

                sku_elements = page.eles('css:[class*="valueItem--"]')
                if not sku_elements:
                    sku_elements = page.eles(
                        'css:[class*="skuItem--"], .J_TSaleProp li, css:[data-property="sku"]')

                if sku_elements:
                    for sku in sku_elements:
                        if sku.attr("data-disabled") == "true": continue
                        sku_name = sku.attr("title") or sku.text.strip()
                        if not sku_name: continue

                        try:
                            sku.click(by_js=True)
                            # 点击每个 SKU 之间的随机间隔，模拟人工选择
                            page.wait(random.uniform(2.0, 3.5))
                            price = "未知"
                            for sel in ['.text--Do8Zgb3q', '.text--LP7Wf49z', 'css:[class*="Price--priceText"]',
                                        '.tb-rmb-num', 'span.price']:
                                loc = page.ele(sel)
                                if loc:
                                    price = loc.text.strip()
                                    if price: break

                            print(f"    - 规格: {sku_name}, 价格: {price}")
                            cursor.execute(
                                f'INSERT INTO {table_name} (名称, 价格, 链接, 获取平台) VALUES (?, ?, ?, ?)',
                                (f"{page_title} - {sku_name}", price, item_url, platform_name))
                        except Exception:
                            pass
                else:
                    price = "未知"
                    for sel in ['.text--LP7Wf49z', '.text--Do8Zgb3q', 'css:[class*="Price--priceText"]', '.tb-rmb-num',
                                'span.price']:
                        loc = page.ele(sel)
                        if loc:
                            price = loc.text.strip()
                            break
                    print(f"    - 默认商品: {page_title}, 价格: {price}")
                    cursor.execute(f'INSERT INTO {table_name} (名称, 价格, 链接, 获取平台) VALUES (?, ?, ?, ?)',
                                   (page_title, price, item_url, platform_name))

            except Exception as e:
                pass

            # 在查看下一个商品前，增加较长、更真实的随机等待间隔
            if index < len(item_ids) - 1:
                wait_time = random.uniform(3.0, 8.0)
                print(f"    [等待 {wait_time:.1f} 秒后打开下一个商品...]")
                page.wait(wait_time)

        conn.commit()
        conn.close()
        print(f"抓取完成并已保存！")
    else:
        print("未能提取到商品。")

    page.disconnect()
