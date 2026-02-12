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

def is_china_friendly(location_str):
    """判断职位是否允许在中国远程"""
    if not location_str:
        return False
    
    # 转换为小写进行模糊匹配
    loc = location_str.lower()
    keywords = ['china', 'asia', 'anywhere', 'worldwide', 'global', 'remote', 'distributed']
    
    # 排除掉明确限制在北美、欧洲等地区的职位
    exclude_keywords = ['us only', 'usa only', 'uk only', 'europe only', 'north america']
    
    # 逻辑：包含关键词 且 不包含排除词
    is_match = any(word in loc for word in keywords)
    is_excluded = any(word in loc for word in exclude_keywords)
    
    return is_match and not is_excluded

def update_readme(jobs):
    df = pd.DataFrame(jobs)
    # 将全部符合条件的 40+ 条数据转成 Markdown
    md_table = df.to_markdown(index=False)
    
    # ... (使用上个回答中的 re.sub 逻辑替换 README 中的 部分)

def save_to_excel(jobs):
    file_name = "remote_jobs_list.xlsx"
    sheet_name = datetime.now().strftime("%Y-%m-%d")
    df = pd.DataFrame(jobs)

    if os.path.exists(file_name):
        # mode='a' 是追加模式，if_sheet_exists='replace' 指如果今天已经跑过一次了，就替换今天的 sheet
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        df.to_excel(file_name, sheet_name=sheet_name, index=False)

if __name__ == "__main__":
    # 这里可以循环调用不同网站的爬虫函数
    all_jobs = scrape_weworkremotely() 
    # all_jobs += scrape_workingnomads() ...
    
    if all_jobs:
        save_to_excel(all_jobs)
