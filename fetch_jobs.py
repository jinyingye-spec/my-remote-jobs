import feedparser
import os

# 定义我们要抓取的 RSS 源（这些都是免费公开的）
SOURCES = {
    "We Work Remotely": "https://weworkremotely.com/remote-jobs.rss",
    "Remotive": "https://remotive.com/remote-jobs/feed"
}

def fetch_and_save():
    content = "# 🌍 海外远程兼职列表\n\n更新时间: {}\n\n".format(os.popen('date').read())
    
    for name, url in SOURCES.items():
        content += f"## 📢 来自 {name}\n\n"
        feed = feedparser.parse(url)
        
        # 只取前 10 条最新的
        for entry in feed.entries[:10]:
            content += f"- **[{entry.title}]({entry.link})**\n"
            content += f"  *发布日期: {entry.published}*\n\n"
    
    # 把结果写进 README.md
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fetch_and_save()
