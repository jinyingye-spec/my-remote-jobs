import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os, re, time

# --- 1. 配置 ---
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# --- 2. 稳定的抓取函数库 ---

def scrape_remote_ok():
    print("正在抓取 Remote OK...")
    url = "https://remoteok.com/api"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        data = res.json()
        jobs = []
        for item in data[1:11]: # 严格限制 10 条
            jobs.append({
                "职位": item.get('position', 'N/A'),
                "公司": item.get('company', 'N/A'),
                "地点": "Worldwide",
                "来源": "RemoteOK",
                "链接": item.get('url', '')
            })
        return jobs
    except: return []

def scrape_wwr():
    print("正在抓取 We Work Remotely...")
    url = "https://weworkremotely.com/remote-jobs.rss"
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')
        jobs = []
        for item in items[:10]: # 严格限制 10 条
            jobs.append({
                "职位": item.title.text.strip(),
                "公司": "WWR",
                "地点": "Remote",
                "来源": "WWR",
                "链接": item.link.text.strip()
            })
        return jobs
    except: return []

def scrape_working_nomads():
    print("正在抓取 Working Nomads...")
    url = "https://www.workingnomads.com/jobsapi/rss/jobs?category=development"
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')
        jobs = []
        for item in items[:10]: # 严格限制 10 条
            jobs.append({
                "职位": item.title.text.strip(),
                "公司": "WorkingNomads",
                "地点": "Global",
                "来源": "WN",
                "链接": item.link.text.strip()
            })
        return jobs
    except: return []

def scrape_just_remote():
    print("正在抓取 JustRemote...")
    # JustRemote 没有公开 RSS，我们尝试通过其职位的列表页解析
    url = "https://justremote.co/remote-developer-jobs"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.job-item')
        jobs = []
        for item in items[:10]: # 严格限制 10 条
            title = item.find('h3').text.strip() if item.find('h3') else "N/A"
            company = item.find('div', class_='company').text.strip() if item.find('div', class_='company') else "N/A"
            link = "https://justremote.co" + item.find('a')['href']
            jobs.append({"职位": title, "公司": company, "地点": "Remote", "来源": "JustRemote", "链接": link})
        return jobs
    except: return []

# --- 3. 保存与更新 ---

def save_and_update(all_jobs):
    if not all_jobs: return
    
    df = pd.DataFrame(all_jobs)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 更新 Excel
    file_name = "remote_jobs_list.xlsx"
    if os.path.exists(file_name):
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=today_str, index=False)
    else:
        df.to_excel(file_name, sheet_name=today_str, index=False)

    # 更新 README
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        md_table = df.to_markdown(index=False)
        start_tag, end_tag = "", ""
        
        if start_tag in content and end_tag in content:
            # 这里的正则逻辑会把两个标签中间的所有旧内容一次性清除并填入新的
            pattern = re.compile(f"{re.escape(start_tag)}.*?{re.escape(end_tag)}", re.DOTALL)
            new_block = f"{start_tag}\n\n### 📅 最后更新时间: {today_str}\n\n{md_table}\n\n{end_tag}"
            updated_content = pattern.sub(new_block, content)
            
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(updated_content)
        print(f"🎉 成功整合抓取了 {len(all_jobs)} 条职位！")

if __name__ == "__main__":
    combined = []
    combined += scrape_remote_ok()
    time.sleep(1)
    combined += scrape_wwr()
    time.sleep(1)
    combined += scrape_working_nomads()
    time.sleep(1)
    combined += scrape_just_remote()
    
    save_and_update(combined)
