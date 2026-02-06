import feedparser
import datetime
import re
import pandas as pd
import os

SOURCES = {
    "We Work Remotely": "https://weworkremotely.com/remote-jobs.rss",
    "Remotive": "https://remotive.com/remote-jobs/feed",
    "Working Nomads": "https://www.workingnomads.com/jobsfeed"
}

def clean_text(text):
    return re.sub('<[^<]+?>', '', text)

def fetch_and_save():
    new_jobs = []
    # 获取当前日期，作为 Sheet 的名称
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    sheet_name = now.strftime('%Y-%m-%d')
    excel_file = "remote_jobs_list.xlsx"
    
    # 1. 抓取最新职位
    for name, url in SOURCES.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            desc = clean_text(entry.summary) if 'summary' in entry else ""
            
            # 过滤逻辑：聚焦远程/兼职/合同
            target_keywords = ["remote", "part-time", "contract", "freelance"]
            if any(word in (title + desc).lower() for word in target_keywords):
                new_jobs.append({
                    "平台": name,
                    "职位名称": title,
                    "地点限制": entry.get('location', 'Global/Remote'),
                    "薪资/待遇": re.search(r'\$\d+k? - \$\d+k?|\$\d+[\d,]*', desc).group() if re.search(r'\$\d+k? - \$\d+k?|\$\d+[\d,]*', desc) else "Check website",
                    "发布时间": entry.published if 'published' in entry else "N/A",
                    "申请链接": entry.link
                })

    new_df = pd.DataFrame(new_jobs)

    # 2. 使用 ExcelWriter 实现追加 Sheet
    if os.path.exists(excel_file):
        # 如果文件存在，使用 openpyxl 引擎以追加模式打开
        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            new_df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        # 如果文件不存在，直接创建
        new_df.to_excel(excel_file, sheet_name=sheet_name, index=False)

    # 3. 更新 README 预览（显示今天抓到的数量）
    content = f"# 🌍 海外远程职位库 (按日期分表)\n\n"
    content += f"> 🤖 自动更新完成。今日 (`{sheet_name}`) 已新增 `{len(new_df)}` 个岗位。\n\n"
    content += f"📊 **[点此下载 Excel 查看历史所有数据](./{excel_file})**\n\n"
    content += f"### 📅 今日岗位预览 ({sheet_name})\n\n"
    content += "| 平台 | 职位名称 | 薪资 | 链接 |\n| :--- | :--- | :--- | :--- |\n"
    
    for _, job in new_df.head(15).iterrows():
        content += f"| {job['平台']} | {job['职位名称']} | {job['薪资/待遇']} | [查看]({job['申请链接']}) |\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fetch_and_save()
