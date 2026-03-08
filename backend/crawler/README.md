# 爬虫模块说明

## 现状

京东和淘宝有较强的反爬机制，直接使用 requests 请求容易被封禁。当前实现包括：

1. **BaseCrawler**：基类，提供 `search_jd`、`search_taobao` 框架
2. **create_sample_data**：创建示例数据，用于开发测试
3. **JDCrawler**：京东爬虫类（待完善解析逻辑）

## 扩展真实爬取

### 方案一：Selenium

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get('https://search.jd.com/Search?keyword=CPU')
# 等待页面加载，解析商品列表
items = driver.find_elements(By.CLASS_NAME, 'gl-item')
```

### 方案二：使用价格聚合网站

可考虑爬取 PCOnline、什么值得买等网站的硬件价格数据，反爬相对宽松。

### 方案三：手动导入

管理员可在后台「配件管理」中手动添加/编辑各配件数据，支持从京东/淘宝复制链接。

## 爬取规格参考

- **CPU**：AMD锐龙全系列、Intel酷睿散片/盒装
- **主板**：华硕、微星、华擎、铭瑄
- **显卡**：AMD 6000/7000/9000、NVIDIA 4000/5000、Intel B500
- **内存**：DDR4/DDR5 各品牌最低10条
- **固态**：PCIe3.0/4.0 500G-1T 各容量最低10条
- **散热**：风冷100元5款，水冷240/360各200-500元10款
- **机箱**：50元1款，100-300元海景房5款+普通5款
- **电源**：海韵、振华 450W/550W/650W/750W/850W 金牌全模组各1款
