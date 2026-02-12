import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re
import time

# 通用请求头，防止被封
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def is_china_friendly(location_str):
    if not location_str: return True
    loc = location_str.lower()
    keywords = ['china', 'asia', 'anywhere', 'worldwide', 'global', 'remote', 'distributed']
    exclude_keywords = ['us only', 'usa only', 'uk only', 'europe only', 'north america']
    return any(word in loc for word in keywords) and not any(word in loc for word in exclude_keywords)

# --- 各大网站爬取逻辑 ---

def scrape_weworkremotely():
    print("正在爬取 We Work Remotely...")
    url = "https://weworkremotely.com/remote-jobs/search?term=developer"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = []
        for item in soup.select('.list-container section ul li'):
            if 'view-all' in item.get('class', []): continue
            title = item.find('span', class_='title').text.strip() if item.find('span', class_='title') else "N/A"
            company = item.find('span', class_='company').text.strip() if item.find('span', class_='company') else "N/A"
            region = item.find('span', class_='region').text.strip() if item.find('span', class_='region') else "Global"
            link = "https://weworkremotely.com" + item.find('a', recursive=False)['href']
            jobs.append({"职位": title, "公司": company, "地点": region, "来源": "WWR", "链接": link})
        return jobs
    except: return []

def scrape_weworkremotely():
    print("正在爬取 We Work Remotely...")
    # 搜索 developer 肯定有结果，china 可能搜不到
    url = "https://weworkremotely.com/remote-jobs/search?term=developer"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = []
        # WWR 的真实结构：寻找所有 class 包含 job 的 li
        items = soup.find_all('li', class_='feature') + soup.find_all('li', class_='')
        for item in items:
            title_tag = item.find('span', class_='title')
            if not title_tag: continue
            
            title = title_tag.text.strip()
            company = item.find('span', class_='company').text.strip() if item.find('span', class_='company') else "N/A"
            region = item.find('span', class_='region').text.strip() if item.find('span', class_='region') else "Global"
            link_tag = item.find('a', recursive=False)
            if not link_tag: continue
            link = "https://weworkremotely.com" + link_tag['href']
            
            jobs.append({"职位": title, "公司": company, "地点": region, "来源": "WWR", "链接": link})
        print(f"WWR 抓取成功，找到 {len(jobs)} 条")
        return jobs
    except Exception as e:
        print(f"WWR 报错: {e}")
        return []

def scrape_justremote():
    print("正在爬取 JustRemote...")
    url = "https://justremote.co/remote-developer-jobs"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = []
        for item in soup.select('.job-item'):
            title = item.find('h3').text.strip()
            company = item.find('div', class_='company').text.strip()
            # 这里的地点通常在特定的 span 里
            jobs.append({"职位": title, "公司": company, "地点": "Remote", "来源": "JustRemote", "链接": "https://justremote.co" + item.find('a')['href']})
        return jobs
    except: return []

# --- 存储与更新逻辑 (保持不变但确保被调用) ---

def save_and_update(all_jobs):
    if not all_jobs:
        print("全部抓取结果为空，请检查网络或网站结构")
        return

    # 1. 过滤 & 每个网站取 8 条
    df = pd.DataFrame(all_jobs)
    filtered_jobs = [j for j in all_jobs if is_china_friendly(j['地点'])]
    
    # 按来源分组取前8条
    final_list = []
    sources = set([j['来源'] for j in filtered_jobs])
    for s in sources:
        final_list.extend([j for j in filtered_jobs if j['来源'] == s][:8])

    df_final = pd.DataFrame(final_list)

    # 2. 保存 Excel
    file_name = "remote_jobs_list.xlsx"
    sheet_name = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(file_name):
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_final.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        df_final.to_excel(file_name, sheet_name=sheet_name, index=False)

    # 3. 更新 README
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        md_table = df_final.to_markdown(index=False)
        start_tag, end_tag = "", ""
        new_content = f"{start_tag}\n\n### 更新日期: {sheet_name}\n\n{md_table}\n\n{end_tag}"
        updated_content = re.sub(f"{re.escape(start_tag)}.*?{re.escape(end_tag)}", new_content, content, flags=re.DOTALL)
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(updated_content)
    print("Excel 和 README 已更新成功！")

if __name__ == "__main__":
    combined_jobs = []
    combined_jobs += scrape_weworkremotely()
    time.sleep(2)
    combined_jobs += scrape_workingnomads()
    time.sleep(2)
    combined_jobs += scrape_justremote()
    
    save_and_update(combined_jobs)
