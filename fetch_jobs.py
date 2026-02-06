import feedparser
import datetime

# 数据源
SOURCES = {
    "We Work Remotely": "https://weworkremotely.com/remote-jobs.rss",
    "Remotive": "https://remotive.com/remote-jobs/feed"
}

def fetch_and_save():
    # 获取当前北京时间 (UTC+8)
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

    # 准备 Markdown 头部
    content = f"# 🌍 海外远程兼职/合同工列表\n\n"
    content += f"> 🤖 机器人最后更新于: `{dt_string}` (北京时间)\n\n"
    content += "| 来源平台 | 职位名称 | 发布时间 | 申请链接 |\n"
    content += "| :--- | :--- | :--- | :--- |\n"
    
    found_jobs = False

    for name, url in SOURCES.items():
        feed = feedparser.parse(url)
        
        for entry in feed.entries[:15]:
            title = entry.title
            # 简单的关键词筛选（可选，如果想看全部，可以删掉下面这行 if 判断）
            # if any(word in title.lower() for word in ["remote", "part-time", "contract", "freelance"]):
            
            # 清理标题中的逗号，防止破坏表格格式
            clean_title = title.replace("|", "-")
            link = entry.link
            pub_date = entry.published[:16] # 截取日期部分
            
            content += f"| {name} | {clean_title} | {pub_date} | [点击申请]({link}) |\n"
            found_jobs = True

    if not found_jobs:
        content += "| N/A | 暂时没有发现新职位 | - | - |\n"

    # 写入文件
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fetch_and_save()
