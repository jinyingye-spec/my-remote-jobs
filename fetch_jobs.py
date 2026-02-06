import feedparser
import datetime
import re
import pandas as pd
import os
import requests

# 1. RSS 数据源
RSS_SOURCES = {
    "We Work Remotely": "https://weworkremotely.com/remote-jobs.rss",
    "Working Nomads": "https://www.workingnomads.com/jobsfeed",
    "DailyRemote": "https://dailyremote.com/remote-jobs.rss",
    "JustRemote": "https://justremote.co/remote-jobs.rss",
    "Upwork (Global)": "https://www.upwork.com/ab/feed/jobs/rss?q=remote",
    "Freelancer": "https://www.freelancer.com/rss.xml"
}

def clean_text(text):
    if not text: return ""
    return re.sub('<[^<]+?>', '', text)

def fetch_remotive():
    """专门为 Remotive 写的 API 抓取逻辑"""
    jobs = []
    try:
        # Remotive 官方提供的免费公开 API
        response = requests.get("https://remotive.com/api/remote-jobs?limit=15")
        if response.status_code == 200:
            data = response.json()
            for item in data.get('jobs', []):
                jobs.append({
                    "平台": "Remotive",
                    "优先级": "⭐ High" if "anywhere" in item.get('candidate_required_location', '').lower() else "Normal",
                    "职位名称": item.get('title'),
                    "地点/限制": item.get('candidate_required_location', 'Remote'),
                    "薪资/计费": item.get('salary', 'Check website'),
                    "发布时间": item.get('publication_date', '')[:10],
                    "申请链接": item.get('url')
                })
    except Exception as e:
        print(f"Remotive 抓取失败: {e}")
    return jobs

def fetch_and_save():
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    sheet_name = now.strftime('%Y-%m-%d')
    excel_file = "remote_jobs_list.xlsx"
    
    all_platform_data = []

    # A. 抓取 RSS 源
    for name, url in RSS_SOURCES.items():
        print(f"正在抓取: {name}...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]: # 每个平台取 10 条
            title = entry.title
            desc = clean_text(entry.summary) if 'summary' in entry else ""
            
            # 优先级逻辑
            priority = "Normal"
            location = "Remote"
            if any(word in (title + desc).lower() for word in ["anywhere", "worldwide", "global", "china"]):
                priority = "⭐ High"
                location = "🌍 Global/Anywhere"

            all_platform_data.append({
                "平台": name,
                "优先级": priority,
                "职位名称": title,
                "地点/限制": location,
                "薪资/计费": re.search(r'\$\d+(?:k|/hr| - \$\d+)?', desc + title).group() if re.search(r'\$\d+(?:k|/hr| - \$\d+)?', desc + title) else "See Link",
                "发布时间": entry.get('published', 'N/A')[:16],
                "申请链接": entry.link
            })

    # B. 抓取 Remotive
    print("正在抓取: Remotive...")
    all_platform_data.extend(fetch_remotive())

    new_df = pd.DataFrame(all_platform_data)

    # 3. 写入 Excel (新开 Sheet)
    if os.path.exists(excel_file):
        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            new_df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        new_df.to_excel(excel_file, sheet_name=sheet_name, index=False)

    # 4. 更新 README 预览
    content = f"# 🌍 全球远程/项目制职位汇总 (含 Remotive)\n\n"
    content += f"> 🤖 更新时间: `{now.strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
    content += f"📊 **[点此下载 Excel 表格 (包含所有历史日期分表)](./{excel_file})**\n\n"
    content += "### 🚀 今日高优先级推荐 (Anywhere)\n\n"
    content += "| 平台 | 职位名称 | 地点限制 | 链接 |\n| :--- | :--- | :--- | :--- |\n"
    
    high_prio = [j for j in all_platform_data if j['优先级'] == "⭐ High"]
    for job in high_prio[:15]:
        content += f"| {job['平台']} | {job['职位名称']} | {job['地点/限制']} | [申请]({job['申请链接']}) |\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fetch_and_save()
