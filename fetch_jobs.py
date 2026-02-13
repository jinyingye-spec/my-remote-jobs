import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os, re, time

# --- 1. 增强版请求配置 ---
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# --- 2. 稳健的抓取函数 ---

def scrape_remote_ok():
    print("正在爬取 Remote OK (API模式)...")
    url = "https://remoteok.com/api" # 使用其公开API，比网页更稳
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        data = res.json()
        jobs = []
        # API第一个元素通常是声明，跳过
        for item in data[1:15]:
            jobs.append({
                "职位": item.get('position', 'N/A'),
                "公司": item.get('company', 'N/A'),
                "地点": "Worldwide",
                "来源": "RemoteOK",
                "链接": item.get('url', '')
            })
        print(f"Remote OK 抓取成功: {len(jobs)} 条")
        return jobs
    except: return []

def scrape_wwr_rss():
    print("正在爬取 We Work Remotely (RSS)...")
    url = "https://weworkremotely.com/remote-jobs.rss"
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')
        jobs = []
        for item in items[:15]:
            jobs.append({
                "职位": item.title.text.strip(),
                "公司": "WWR",
                "地点": "Remote",
                "来源": "WWR",
                "链接": item.link.text.strip()
            })
        print(f"WWR 抓取成功: {len(jobs)} 条")
        return jobs
    except: return []

# --- 3. 核心保存与替换逻辑 ---

def save_and_update(all_jobs):
    if not all_jobs:
        all_jobs = [{"职位": "正在等待新职位发布...", "公司": "-", "地点": "-", "来源": "System", "链接": "#"}]

    df = pd.DataFrame(all_jobs)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # A. 更新 Excel (保持不变)
    file_name = "remote_jobs_list.xlsx"
    if os.path.exists(file_name):
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=today_str, index=False)
    else:
        df.to_excel(file_name, sheet_name=today_str, index=False)

    # B. 更新 README (彻底解决重复问题)
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        md_table = df.to_markdown(index=False)
        start_tag, end_tag = "", ""
        
        if start_tag in content and end_tag in content:
            # 这里的正则会吃掉两个标签之间的所有内容，包括旧的日期和表格
            pattern = re.compile(f"{re.escape(start_tag)}.*?{re.escape(end_tag)}", re.DOTALL)
            new_block = f"{start_tag}\n\n### 📅 最后更新: {today_str}\n\n{md_table}\n\n{end_tag}"
            updated_content = pattern.sub(new_block, content)
            
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(updated_content)
            print("✅ README.md 更新成功！")

if __name__ == "__main__":
    data = []
    data += scrape_remote_ok()
    time.sleep(2)
    data += scrape_wwr_rss()
    save_and_update(data)
