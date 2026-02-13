import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os, re, time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# --- 抓取函数：每个都强制只返回前 10 个 ---

def scrape_remote_ok():
    print("正在抓取 Remote OK...")
    try:
        res = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=15)
        data = res.json()
        jobs = []
        for item in data[1:11]: # 只取 API 返回的前 10 个有效职位
            jobs.append({
                "职位": item.get('position', 'N/A'),
                "公司": item.get('company', 'N/A'),
                "来源": "RemoteOK",
                "链接": item.get('url', '')
            })
        return jobs
    except: return []

def scrape_wwr():
    print("正在抓取 We Work Remotely...")
    try:
        res = requests.get("https://weworkremotely.com/remote-jobs.rss", timeout=15)
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')
        jobs = []
        for item in items[:10]: # 强制限制 10 条
            jobs.append({
                "职位": item.title.text.strip(),
                "公司": "WWR",
                "来源": "WWR",
                "链接": item.link.text.strip()
            })
        return jobs
    except: return []

def scrape_working_nomads():
    print("正在抓取 Working Nomads...")
    try:
        res = requests.get("https://www.workingnomads.com/jobsapi/rss/jobs?category=development", timeout=15)
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')
        jobs = []
        for item in items[:10]: # 强制限制 10 条
            jobs.append({
                "职位": item.title.text.strip(),
                "公司": "WorkingNomads",
                "来源": "WN",
                "链接": item.link.text.strip()
            })
        return jobs
    except: return []

# --- 统一更新逻辑 ---

def save_and_update(all_jobs):
    if not all_jobs: return
    
    # 转换为 DataFrame 并整理
    df = pd.DataFrame(all_jobs)
    # 只保留这几列，让表格在手机端看也不挤
    df = df[["职位", "公司", "来源", "链接"]] 
    
    today_str = datetime.now().strftime("%Y-%m-%d")

    # A. 保存 Excel
    file_name = "remote_jobs_list.xlsx"
    if os.path.exists(file_name):
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=today_str, index=False)
    else:
        df.to_excel(file_name, sheet_name=today_str, index=False)

    # B. 更新 README (使用正则彻底替换)
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        md_table = df.to_markdown(index=False)
        start_tag, end_tag = "", ""
        
        if start_tag in content and end_tag in content:
            pattern = re.compile(f"{re.escape(start_tag)}.*?{re.escape(end_tag)}", re.DOTALL)
            new_block = f"{start_tag}\n\n### 📅 本次聚合最新职位 ({today_str})\n\n{md_table}\n\n{end_tag}"
            updated_content = pattern.sub(new_block, content)
            
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(updated_content)
        print(f"✅ 汇总完成，总计展示 {len(all_jobs)} 条精选职位")

if __name__ == "__main__":
    combined = []
    # 依次添加，如果某个站挂了，也不影响别的站
    combined += scrape_wwr()
    combined += scrape_working_nomads()
    combined += scrape_remote_ok()
    
    save_and_update(combined)
