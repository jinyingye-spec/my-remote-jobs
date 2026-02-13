import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re
import time

# --- 1. 基础配置 ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# --- 2. 爬取函数 (统一采用 RSS 模式，最稳定) ---

def scrape_wwr_rss():
    print("正在通过 RSS 爬取 We Work Remotely...")
    url = "https://weworkremotely.com/remote-jobs.rss"
    jobs = []
    try:
        res = requests.get(url, timeout=15)
        # 使用简单的正则或内置解析，减少对 lxml 的依赖报错
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')
        for item in items[:15]: # 取前15条
            jobs.append({
                "职位": item.title.text.strip(),
                "公司": "WWR",
                "地点": "Remote",
                "来源": "WWR",
                "链接": item.link.text.strip()
            })
    except Exception as e:
        print(f"WWR RSS 抓取失败: {e}")
    return jobs

def scrape_upwork_rss():
    print("正在通过 RSS 爬取 Upwork...")
    # 搜索 'python' 相关的远程职位
    url = "https://www.upwork.com/ab/feed/jobs/rss?q=python&sort=recency"
    jobs = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')
        for item in items[:10]:
            jobs.append({
                "职位": item.title.text.strip()[:60] + "...",
                "公司": "Upwork Client",
                "地点": "Worldwide",
                "来源": "Upwork",
                "链接": item.link.text.strip()
            })
    except Exception as e:
        print(f"Upwork RSS 抓取失败: {e}")
    return jobs

# --- 3. 核心保存逻辑 ---

def save_and_update(all_jobs):
    if not all_jobs:
        # 如果啥也没抓到，生成一条保底数据，防止 Action 报错
        all_jobs = [{"职位": "暂无新职位 (检查源)", "公司": "-", "地点": "-", "来源": "System", "链接": "#"}]

    df = pd.DataFrame(all_jobs)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # A. 保存到 Excel
    file_name = "remote_jobs_list.xlsx"
    try:
        if os.path.exists(file_name):
            with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=today_str, index=False)
        else:
            df.to_excel(file_name, sheet_name=today_str, index=False)
    except Exception as e:
        print(f"Excel 保存失败: {e}")

    # B. 更新 README
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 将职位转为 Markdown 表格
        md_table = df.to_markdown(index=False)
        start_tag, end_tag = "", ""
        
        if start_tag in content and end_tag in content:
            new_block = f"{start_tag}\n\n### 📅 更新日期: {today_str}\n\n{md_table}\n\n{end_tag}"
            # 使用正则替换，确保只替换一对标签之间的内容
            pattern = f"{re.escape(start_tag)}.*?{re.escape(end_tag)}"
            updated_content = re.sub(pattern, new_block, content, flags=re.DOTALL)
            
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(updated_content)
            print("✅ README.md 更新成功！")
        else:
            print("❌ 错误：README.md 中找不到暗号标签！")

# --- 4. 运行入口 (严格对应上面的函数名) ---

if __name__ == "__main__":
    print(f"--- 任务启动: {datetime.now()} ---")
    combined_data = []
    
    # 只调用上面定义过的函数
    combined_data += scrape_wwr_rss()
    time.sleep(2)
    combined_data += scrape_upwork_rss()
    
    # 执行保存
    save_and_update(combined_data)
    print("--- 任务结束 ---")
