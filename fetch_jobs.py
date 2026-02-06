import feedparser
import datetime
import re
import pandas as pd
import os

# 1. 配置你要求的全部数据源
SOURCES = {
    "We Work Remotely": "https://weworkremotely.com/remote-jobs.rss",
    "Working Nomads": "https://www.workingnomads.com/jobsfeed",
    "DailyRemote": "https://dailyremote.com/remote-jobs.rss",
    "JustRemote": "https://justremote.co/remote-jobs.rss",
    # 自由职业平台通过 RSS 聚合源接入（模拟抓取项目类）
    "Upwork (Global)": "https://www.upwork.com/ab/feed/jobs/rss?q=remote",
    "Freelancer (Projects)": "https://www.freelancer.com/rss.xml"
}

def clean_text(text):
    return re.sub('<[^<]+?>', '', text)

def fetch_and_save():
    # 获取当前日期用于 Sheet 命名
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    sheet_name = now.strftime('%Y-%m-%d')
    excel_file = "remote_jobs_list.xlsx"
    
    final_data = []

    for name, url in SOURCES.items():
        print(f"正在抓取: {name}...")
        feed = feedparser.parse(url)
        
        count = 0
        for entry in feed.entries:
            if count >= 10: # 每个平台最多取 10 个，符合你的要求
                break
                
            title = entry.title
            desc = clean_text(entry.summary) if 'summary' in entry else ""
            link = entry.link
            
            # --- 优先级逻辑 ---
            # 1. 优先标记 Anywhere / Worldwide / China
            location = "Remote / Not Specified"
            priority = "Normal"
            
            location_keywords = ["anywhere", "worldwide", "china", "global", "no office"]
            if any(word in (title + desc).lower() for word in location_keywords):
                location = "🌍 Global/Anywhere"
                priority = "⭐ High (Remote-First)"
            
            # 2. 提取薪资/计费（针对 Upwork 等）
            salary = "See Link"
            # 匹配 $xx/hr 或 $xxx 固定价格
            salary_match = re.search(r'\$\d+(?:k|/hr| - \$\d+)?', desc + title)
            if salary_match:
                salary = salary_match.group()

            final_data.append({
                "平台": name,
                "优先级": priority,
                "职位名称": title,
                "地点/限制": location,
                "薪资/计费": salary,
                "发布时间": entry.published[:16] if 'published' in entry else "N/A",
                "申请链接": link
            })
            count += 1

    new_df = pd.DataFrame(final_data)

    # 3. 写入 Excel (新开 Sheet)
    if os.path.exists(excel_file):
        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            new_df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        new_df.to_excel(excel_file, sheet_name=sheet_name, index=False)

    # 4. 更新 README 预览
    content = f"# 🌍 全球远程/项目制职位汇总\n\n"
    content += f"> 🤖 自动更新时间: `{now.strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
    content += f"📊 **[点此下载最新 Excel 表格 (含历史分表)](./{excel_file})**\n\n"
    
    # 预览高优先级职位
    content += "### 🚀 优先推荐 (Anywhere/Global)\n\n"
    content += "| 平台 | 职位名称 | 薪资/计费 | 链接 |\n| :--- | :--- | :--- | :--- |\n"
    
    high_priority = [j for j in final_data if j['优先级'] == "⭐ High (Remote-First)"]
    for job in high_priority[:15]:
        content += f"| {job['平台']} | {job['职位名称']} | {job['薪资/计费']} | [立即查看]({job['申请链接']}) |\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fetch_and_save()
