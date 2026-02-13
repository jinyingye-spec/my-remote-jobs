import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os, re, time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def scrape_remote_ok():
    print("正在抓取 Remote OK...")
    try:
        res = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=15)
        data = res.json()
        jobs = []
        # 强制切片 data[1:11]，确保只取前10条
        for item in data[1:11]: 
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
        for item in items[:10]: # 限制 10 条
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
        for item in items[:10]: # 限制 10 条
            jobs.append({
                "职位": item.title.text.strip(),
                "公司": "WorkingNomads",
                "来源": "WN",
                "链接": item.link.text.strip()
            })
        return jobs
    except: return []

def save_and_update(all_jobs):
    if not all_jobs: return
    
    # 转换为 DataFrame
    df = pd.DataFrame(all_jobs)
    # 强制只显示以下四列，防止表格过宽
    df = df[["职位", "公司", "来源", "链接"]] 
    
    today_str = datetime.now().strftime("%Y-%m-%d")

    # A. 保存 Excel
    file_name = "remote_jobs_list.xlsx"
    if os.path.exists(file_name):
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=today_str, index=False)
    else:
        df.to_excel(file_name, sheet_name=today_str, index=False)

    # B. 更新 README (核心正则替换)
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        md_table = df.to_markdown(index=False)
        start_tag, end_tag = "", ""
        
        if start_tag in content and end_tag in content:
            # 使用 re.DOTALL 确保跨行匹配，把旧的 300 多行一次性干掉
            pattern = re.compile(f"{re.escape(start_tag)}.*?{re.escape(end_tag)}", re.DOTALL)
            new_block = f"{start_tag}\n\n### 📅 本次精选职位 ({today_str})\n\n{md_table}\n\n{end_tag}"
            updated_content = pattern.sub(new_block, content)
            
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(updated_content)
        print(f"✅ 更新完成，总计展示 {len(all_jobs)} 条各来源精选职位")

if __name__ == "__main__":
    combined = []
    # 建议把 RemoteOK 放在最后，让 WWR 和 WN 优先展示
    combined += scrape_wwr()
    combined += scrape_working_nomads()
    combined += scrape_remote_ok()
    
    save_and_update(combined)
