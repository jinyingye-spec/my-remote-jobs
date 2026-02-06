import feedparser
import datetime
import re

SOURCES = {
    "We Work Remotely": "https://weworkremotely.com/remote-jobs.rss",
    "Remotive": "https://remotive.com/remote-jobs/feed"
}

def clean_text(text):
    # 去除 HTML 标签，方便提取纯文本信息
    return re.sub('<[^<]+?>', '', text)

def fetch_and_save():
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

    content = f"# 🌍 海外远程兼职/合同工列表\n\n"
    content += f"> 🤖 机器人最后更新于: `{dt_string}` (北京时间)\n\n"
    # 增加了：岗位类型、工作城市、福利待遇
    content += "| 来源平台 | 职位名称 | 岗位类型 | 工作城市/限制 | 福利待遇/薪资 | 链接 |\n"
    content += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    for name, url in SOURCES.items():
        feed = feedparser.parse(url)
        
        for entry in feed.entries[:15]:
            title = entry.title.replace("|", "-")
            link = entry.link
            
            # 提取描述内容进行分析
            desc = clean_text(entry.summary) if 'summary' in entry else ""
            
            # 1. 尝试提取岗位类型 (Part-time / Full-time / Contract)
            job_type = "Remote"
            if "part-time" in desc.lower() or "part-time" in title.lower():
                job_type = "⏱️ Part-time"
            elif "contract" in desc.lower() or "contract" in title.lower():
                job_type = "📄 Contract"
            
            # 2. 尝试从 Remotive 这种自带分类的源提取城市/地点限制
            location = "Anywhere"
            if 'location' in entry:
                location = entry.location
            elif "worldwide" in desc.lower():
                location = "🌎 Worldwide"
            
            # 3. 尝试提取薪资或待遇 (寻找 $ 符号)
            benefits = "查看详情"
            salary_match = re.search(r'\$\d+k? - \$\d+k?|\$\d+[\d,]*', desc)
            if salary_match:
                benefits = f"💰 {salary_match.group()}"
            elif "vacation" in desc.lower() or "stock" in desc.lower():
                benefits = "🎁 含福利"

            content += f"| {name} | {title} | {job_type} | {location} | {benefits} | [申请]({link}) |\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fetch_and_save()
