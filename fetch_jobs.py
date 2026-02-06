import feedparser
import datetime
import re
import pandas as pd

# 聚焦全球顶级远程/兼职数据源
SOURCES = {
    "We Work Remotely": "https://weworkremotely.com/remote-jobs.rss",
    "Remotive": "https://remotive.com/remote-jobs/feed",
    "Working Nomads": "https://www.workingnomads.com/jobsfeed"
}

def clean_text(text):
    return re.sub('<[^<]+?>', '', text)

def fetch_and_save():
    all_jobs = []
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    
    for name, url in SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            desc = clean_text(entry.summary) if 'summary' in entry else ""
            
            # --- 核心逻辑：聚焦远程 & 兼职 ---
            # 只抓取标题或描述里包含这些词的岗位
            target_keywords = ["remote", "part-time", "contract", "freelance", "anywhere"]
            if any(word in (title + desc).lower() for word in target_keywords):
                
                # 提取薪资（正则匹配）
                salary = "Check website"
                salary_match = re.search(r'\$\d+k? - \$\d+k?|\$\d+[\d,]*', desc)
                if salary_match:
                    salary = salary_match.group()

                all_jobs.append({
                    "平台": name,
                    "职位名称": title,
                    "地点限制": entry.get('location', 'Global/Remote'),
                    "薪资/待遇": salary,
                    "发布时间": entry.published[:16] if 'published' in entry else "N/A",
                    "申请链接": entry.link
                })

    # 1. 生成 Excel
    df = pd.DataFrame(all_jobs)
    df.to_excel("remote_jobs_list.xlsx", index=False)

    # 2. 生成 README 预览表格
    content = f"# 🌍 海外远程职位列表 (含 Excel 下载)\n\n"
    content += f"更新时间: `{now.strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
    content += f"📊 [点此下载生成的 Excel 文件](./remote_jobs_list.xlsx)\n\n"
    content += "| 平台 | 职位名称 | 薪资 | 链接 |\n| :--- | :--- | :--- | :--- |\n"
    
    for job in all_jobs[:20]: # 网页只预览前20个，剩下的看Excel
        content += f"| {job['平台']} | {job['职位名称']} | {job['薪资/待遇']} | [查看]({job['申请链接']}) |\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fetch_and_save()
