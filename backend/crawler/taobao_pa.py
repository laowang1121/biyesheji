import webbrowser
from scraper import scrape_and_save

def search_taobao():
    keyword = input("请输入要在淘宝搜索的关键词: ")
    if not keyword:
        print("未输入关键词，默认打开淘宝首页。")
        url = "https://www.taobao.com"
        print(f"正在打开网页: {url}...")
        webbrowser.open(url)
    else:
        scrape_and_save(keyword)

if __name__ == "__main__":
    search_taobao()