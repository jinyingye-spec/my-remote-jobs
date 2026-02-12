import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

# 配置要爬取的源 (示例：We Work Remotely)
def scrape_weworkremotely():
    url = "https://weworkremotely.com/remote-jobs/search?term=china" # 搜索包含China的
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []
    
    # 根据网站实际HTML标签提取数据 (此处为示意)
    for job_card in soup.select('.list-container section ul li'):
        title = job_card.find('span', class_='title').text.strip() if job_card.find('span', class_='title') else "N/A"
        company = job_card.find('span', class_='company').text.strip() if job_card.find('span', class_='company') else "N/A"
        link = "https://weworkremotely.com" + job_card.find('a')['href']
        
        jobs.append({
            "职位": title,
            "公司": company,
            "地点": "Remote (China Friendly)",
            "来源": "We Work Remotely",
            "链接": link
        })
    return jobs

def save_to_excel(new_data):
    file_name = "remote_jobs_list.xlsx"
    sheet_name = datetime.now().strftime("%Y-%m-%d") # 用日期作为Sheet名
    
    df = pd.DataFrame(new_data)
    
    # 如果文件已存在，使用 append 模式添加新 Sheet
    if os.path.exists(file_name):
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        # 第一次创建文件
        df.to_excel(file_name, sheet_name=sheet_name, index=False)
    print(f"数据已更新至 Sheet: {sheet_name}")

if __name__ == "__main__":
    # 这里可以循环调用不同网站的爬虫函数
    all_jobs = scrape_weworkremotely() 
    # all_jobs += scrape_workingnomads() ...
    
    if all_jobs:
        save_to_excel(all_jobs)
