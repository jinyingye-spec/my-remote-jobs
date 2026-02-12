import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re
import time

# --- 基础配置 ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def is_china_friendly(location_str):
    """筛选允许中国/亚洲/全球远程的职位"""
    if not location_str: return True
    loc = location_str.lower()
    keywords = ['china', 'asia', 'anywhere', 'worldwide', 'global', 'remote', 'distributed', 'apac']
    exclude_keywords = ['us only', 'usa only', 'uk only', 'europe only', 'north america', 'canada only']
    return any(word in loc for word in keywords) and not any(word in loc for word in exclude_keywords)

# --- 1. We Work Remotely 抓取逻辑 ---
def scrape_weworkremotely():
    print("正在爬取 We Work Remotely...")
    url = "https://weworkremotely.com/remote-jobs/search?term=developer"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = []
        # 定位所有职位列表中的链接
        links = soup.select('section.jobs article ul li a')
        for a in links:
            if 'view-all' in a.get('class', []): continue
            li = a.find_parent('li')
            title = li.find('span', class_='title').text.strip() if li.find('span', class_='title') else "N/A"
            company = li.find('span', class_='company').text.strip() if li.find('span', class_='company') else "N/A"
            region = li.find('span', class_='region').text.strip() if li.find('span', class_='region') else "Global"
            jobs.append({"职位": title, "公司": company, "地点": region, "来源": "WWR", "链接": "https://weworkremotely.com" + a['href']})
        print(f"WWR 抓取成功: {len(jobs)} 条")
        return jobs
    except Exception as e:
        print(f"WWR 出错: {e}"); return []

# --- 2. Working Nomads 抓取逻辑 ---
def scrape_workingnomads():
    print("正在爬取 Working Nomads...")
    url = "https://www.workingnomads.com/jobs?category=development"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = []
        items = soup.select('.job-card') # 根据该网站最新结构调整
        for item in items:
            title = item.find('h2').text.strip() if item.find('h2') else "N/A"
            company = item.find('div', class_='company').text.strip() if item.find('div', class_='company') else "N/A"
            # Working Nomads 默认大多数是 Global
            jobs.append({"职位": title, "公司": company, "地点": "Global", "来源": "Working Nomads", "链接": "https://www.workingnomads.com" + item.find('a')['href']})
        print(f"Working Nomads 抓取成功: {len(jobs)} 条")
        return jobs
    except Exception as e:
        print(f"Working Nomads 出错: {e}"); return []

# --- 3. JustRemote 抓取逻辑 ---
def scrape_justremote():
    print("正在爬取 JustRemote...")
    url = "https://justremote.co/remote-developer-jobs"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        jobs = []
        items = soup.select('.job-item')
        for item in items:
            title = item.find('h3').text.strip() if item.find('h3') else "N/A"
            company = item.find('div', class_='company').text.strip() if item.find('div', class_='company') else "N/A"
            jobs.append({"职位": title, "公司": company, "地点": "Remote", "来源": "JustRemote", "链接": "https://justremote.co" + item.find('a')['href']})
        print(f"JustRemote 抓取成功: {len(jobs)} 条")
        return jobs
    except Exception as e:
        print(f"JustRemote 出错: {e}"); return []

# --- 4. 保存与更新流程 ---
def save_and_update(all_jobs):
    if not all_jobs:
        print("所有网站均未抓取到数据，跳过更新。")
        return

    # 过滤地点并取每个来源的前8条
    filtered_jobs = [j for j in all_jobs if is_china_friendly(j['地点'])]
    
    final_list = []
    sources = set([j['来源'] for j in filtered_jobs])
    for s in sources:
        final_list.extend([j for j in filtered_jobs if j['来源'] == s][:8])

    df_final = pd.DataFrame(final_list)
    sheet_name = datetime.now().strftime("%Y-%m-%d")

    # 更新 Excel
    file_name = "remote_jobs_list.xlsx"
    if os.path.exists(file_name):
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_final.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        df_final.to_excel(file_name, sheet_name=sheet_name, index=False)

    # 更新 README
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        md_table = df_final.to_markdown(index=False)
        start_tag, end_tag = "", ""
        if start_tag in content:
            pattern = f"{re.escape(start_tag)}.*?{re.escape(end_tag)}"
            new_content = f"{start_tag}\n\n### 更新日期: {sheet_name}\n\n{md_table}\n\n{end_tag}"
            updated_content = re.sub(pattern, new_content, content, flags=re.DOTALL)
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(updated_content)
        print("Excel 和 README 已同步更新！")

# --- 主程序入口 ---
if __name__ == "__main__":
    combined_jobs = []
    
    # 依次调用函数，确保每个函数在上方都有定义
    combined_jobs += scrape_weworkremotely()
    time.sleep(2)
    combined_jobs += scrape_workingnomads()
    time.sleep(2)
    combined_jobs += scrape_justremote()
    
    save_and_update(combined_jobs)
