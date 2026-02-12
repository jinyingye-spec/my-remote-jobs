import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re
import time

# --- 1. 爬虫函数 (以 We Work Remotely 为例) ---
def scrape_weworkremotely():
    print("正在抓取 We Work Remotely...")
    url = "https://weworkremotely.com/remote-jobs/search?term=china"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = []
        # WWR 的结构：每个 job 都在 li 标签里
        for job_card in soup.select('.list-container section ul li'):
            if 'view-all' in job_card.get('class', []): continue
            
            title = job_card.find('span', class_='title').text.strip() if job_card.find('span', class_='title') else "N/A"
            company = job_card.find('span', class_='company').text.strip() if job_card.find('span', class_='company') else "N/A"
            # 这里的地点爬取逻辑需要根据实际网页调整，WWR 通常在 region 类名下
            region = job_card.find('span', class_='region').text.strip() if job_card.find('span', class_='region') else "Global"
            link_tag = job_card.find('a', recursive=False) or job_card.select_one('a')
            link = "https://weworkremotely.com" + link_tag['href'] if link_tag else ""
            
            jobs.append({
                "职位": title,
                "公司": company,
                "地点": region,
                "来源": "We Work Remotely",
                "链接": link
            })
        return jobs
    except Exception as e:
        print(f"WWR 抓取出错: {e}")
        return []

# --- 2. 地点过滤逻辑 ---
def is_china_friendly(location_str):
    if not location_str: return True # 没写地点的通常是 Global
    loc = location_str.lower()
    keywords = ['china', 'asia', 'anywhere', 'worldwide', 'global', 'remote', 'distributed']
    exclude_keywords = ['us only', 'usa only', 'uk only', 'europe only', 'north america', 'canada only']
    
    is_match = any(word in loc for word in keywords)
    is_excluded = any(word in loc for word in exclude_keywords)
    return is_match and not is_excluded

# --- 3. 更新 README 逻辑 ---
def update_readme(jobs):
    if not jobs:
        print("没有新职位，跳过 README 更新")
        return
    
    df = pd.DataFrame(jobs)
    # 转换为 Markdown 表格
    md_table = df.to_markdown(index=False)
    
    start_tag = ""
    end_tag = ""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    new_content = f"{start_tag}\n\n> **最后更新时间: {now_str} (UTC)**\n\n{md_table}\n\n{end_tag}"
    
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查标记是否存在
        if start_tag in content and end_tag in content:
            pattern = f"{re.escape(start_tag)}.*?{re.escape(end_tag)}"
            updated_content = re.sub(pattern, new_content, content, flags=re.DOTALL)
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(updated_content)
            print("README.md 已更新")
        else:
            print("错误：README.md 中找不到 标记")

# --- 4. 保存到 Excel 逻辑 ---
def save_to_excel(jobs):
    file_name = "remote_jobs_list.xlsx"
    sheet_name = datetime.now().strftime("%Y-%m-%d")
    df = pd.DataFrame(jobs)

    if os.path.exists(file_name):
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        df.to_excel(file_name, sheet_name=sheet_name, index=False)
    print(f"Excel 已同步到 Sheet: {sheet_name}")

# --- 5. 主运行流程 ---
if __name__ == "__main__":
    final_jobs = []
    
    # 获取各个源的数据
    sources = {
        "We Work Remotely": scrape_weworkremotely,
        # 这里以后可以继续添加其他函数：
        # "Working Nomads": scrape_workingnomads, 
    }
    
    for name, func in sources.items():
        raw_jobs = func()
        # 过滤地点
        filtered = [j for j in raw_jobs if is_china_friendly(j.get('地点', ''))]
        # 每个网站取前 8 条
        sampled = filtered[:8]
        final_jobs.extend(sampled)
        print(f"{name}: 找到 {len(filtered)} 条符合条件的职位，选取前 {len(sampled)} 条")
        time.sleep(2) # 稍微停顿，防封
    
    if final_jobs:
        save_to_excel(final_jobs)
        update_readme(final_jobs)
    else:
        print("本次运行未抓取到任何符合条件的职位数据。")
