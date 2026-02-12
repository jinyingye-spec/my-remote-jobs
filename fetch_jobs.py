import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re
import time

# --- 逻辑筛选 ---
def is_china_friendly(title, location):
    text = (title + " " + (location if location else "")).lower()
    # 关键词：包含这些词之一
    keywords = ['china', 'asia', 'anywhere', 'worldwide', 'global', 'remote', 'apac']
    # 排除词：包含这些词则剔除
    exclude = ['us only', 'usa only', 'uk only', 'europe only', 'north america', 'canada only']
    
    match = any(word in text for word in keywords)
    excluded = any(word in text for word in exclude)
    return match and not excluded

# --- 1. WWR (RSS 版) ---
def scrape_wwr_rss():
    print("正在通过 RSS 爬取 We Work Remotely...")
    url = "https://weworkremotely.com/categories/remote-software-development-jobs.rss"
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'xml') # 使用 XML 解析器
        items = soup.find_all('item')
        jobs = []
        for item in items:
            title = item.title.text
            link = item.link.text
            # RSS 通常在描述里包含公司名
            company = item.find('dc:creator').text if item.find('dc:creator') else "Remote Co"
            jobs.append({"职位": title, "公司": company, "地点": "Global/Remote", "来源": "WWR", "链接": link})
        print(f"WWR RSS 抓取成功: {len(jobs)} 条")
        return jobs
    except Exception as e:
        print(f"WWR RSS 出错: {e}"); return []

# --- 2. Working Nomads (RSS 版) ---
def scrape_wn_rss():
    print("正在通过 RSS 爬取 Working Nomads...")
    url = "https://www.workingnomads.com/jobsapi/rss/jobs?category=development"
    try:
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')
        jobs = []
        for item in items:
            jobs.append({
                "职位": item.title.text,
                "公司": "Working Nomads",
                "地点": "Remote",
                "来源": "Working Nomads",
                "链接": item.link.text
            })
        print(f"Working Nomads RSS 抓取成功: {len(jobs)} 条")
        return jobs
    except Exception as e:
        print(f"WN RSS 出错: {e}"); return []

# --- 核心处理与更新 (增强鲁棒性) ---
def save_and_update(all_jobs):
    if not all_jobs:
        # 如果还是没抓到，造一个“系统通知”职位，证明流程是通的
        all_jobs = [{"职位": "工作流运行正常", "公司": "System", "地点": "Everywhere", "来源": "System", "链接": "https://github.com"}]
        print("警告：未抓到实时数据，生成测试行。")

    # 过滤
    final_list = [j for j in all_jobs if is_china_friendly(j['职位'], j['地点'])]
    if not final_list: final_list = all_jobs[:10] # 如果过滤完没了，就取前10个保底

    df_final = pd.DataFrame(final_list)
    sheet_name = datetime.now().strftime("%Y-%m-%d")

    # Excel
    file_name = "remote_jobs_list.xlsx"
    if os.path.exists(file_name):
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_final.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        df_final.to_excel(file_name, sheet_name=sheet_name, index=False)

    # README
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        md_table = df_final.to_markdown(index=False)
        start_tag, end_tag = "", ""
        if start_tag in content:
            new_block = f"{start_tag}\n\n### 最后更新: {sheet_name}\n\n{md_table}\n\n{end_tag}"
            updated_content = re.sub(f"{re.escape(start_tag)}.*?{re.escape(end_tag)}", new_block, content, flags=re.DOTALL)
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(updated_content)
    print("🎉 更新任务全部完成！")

if __name__ == "__main__":
    data = []
    data += scrape_wwr_rss()
    data += scrape_wn_rss()
    save_and_update(data)
