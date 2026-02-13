import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os, re, time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def scrape_remote_ok():
    print(">>> 正在启动 Remote OK 抓取...")
    try:
        res = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=15)
        data = res.json()
        # 强制：只取 API 返回的前 10 个（跳过第一个法律声明）
        subset = data[1:11] 
        jobs = [{"职位": j.get('position'), "公司": j.get('company'), "来源": "RemoteOK", "链接": j.get('url')} for j in subset]
        print(f"DEBUG: RemoteOK 成功获取 {len(jobs)} 条")
        return jobs
    except Exception as e:
        print(f"DEBUG: RemoteOK 报错 - {e}")
        return []

def scrape_wwr():
    print(">>> 正在启动 WWR 抓取...")
    try:
        res = requests.get("https://weworkremotely.com/remote-jobs.rss", timeout=15)
        # 将 'xml' 改为 'xml' 或 'html.parser'，但前提是安装了 lxml
        soup = BeautifulSoup(res.text, 'xml') 
        items = soup.find_all('item')[:10]
        jobs = [{"职位": i.title.text, "公司": "WWR", "来源": "WWR", "链接": i.link.text} for i in items]
        print(f"DEBUG: WWR 成功获取 {len(jobs)} 条")
        return jobs
    except Exception as e:
        print(f"DEBUG: WWR 报错 - {e}")
        return []

def scrape_working_nomads():
    print(">>> 正在启动 Working Nomads 抓取...")
    try:
        res = requests.get("https://www.workingnomads.com/jobsapi/rss/jobs?category=development", timeout=15)
        soup = BeautifulSoup(res.text, 'xml') # 同样确保这里能用 xml
        items = soup.find_all('item')[:10]
        jobs = [{"职位": i.title.text, "公司": "WorkingNomads", "来源": "WN", "链接": i.link.text} for i in items]
        print(f"DEBUG: WN 成功获取 {len(jobs)} 条")
        return jobs
    except Exception as e:
        print(f"DEBUG: WN 报错 - {e}")
        return []

def save_and_update(all_jobs):
    if not all_jobs:
        print("CRITICAL: 所有源均为空，不更新文件。")
        return

    # 最终防御：不管前面发生了什么，总表只留前 30 行
    final_jobs = all_jobs[:30]
    df = pd.DataFrame(final_jobs)[["职位", "公司", "来源", "链接"]]
    today = datetime.now().strftime("%Y-%m-%d")

    # A. 更新 Excel
    try:
        file_name = "remote_jobs_list.xlsx"
        if os.path.exists(file_name):
            with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=today, index=False)
        else:
            df.to_excel(file_name, sheet_name=today, index=False)
    except: pass

    # B. 更新 README
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        start_tag, end_tag = "", ""
        if start_tag in content and end_tag in content:
            md_table = df.to_markdown(index=False)
            new_block = f"{start_tag}\n\n### 📅 更新: {today}\n\n{md_table}\n\n{end_tag}"
            # 使用 re.DOTALL 确保能替换中间多行数据
            updated = re.sub(f"{re.escape(start_tag)}.*?{re.escape(end_tag)}", new_block, content, flags=re.DOTALL)
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(updated)
            print(f"SUCCESS: 已写入 {len(final_jobs)} 条职位到 README")

if __name__ == "__main__":
    combined = []
    # 调整顺序：把最稳的 RSS 放前面
    combined += scrape_wwr()
    combined += scrape_working_nomads()
    combined += scrape_remote_ok()
    
    save_and_update(combined)
