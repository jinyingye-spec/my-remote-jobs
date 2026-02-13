import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os, re, time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def scrape_remote_ok():
    try:
        res = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=15)
        # 严格限制：只取前 10 条
        data = res.json()[1:11] 
        return [{"职位": j.get('position'), "公司": j.get('company'), "来源": "RemoteOK", "链接": j.get('url')} for j in data]
    except: return []

def scrape_wwr():
    try:
        res = requests.get("https://weworkremotely.com/remote-jobs.rss", timeout=15)
        # 使用 lxml 解析，确保你在 main.yml 里加了 lxml
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')[:10]
        return [{"职位": i.title.text, "公司": "WWR", "来源": "WWR", "链接": i.link.text} for i in items]
    except: return []

def save_and_update(all_jobs):
    if not all_jobs: return
    
    # 汇总并再次强制截断总数
    df = pd.DataFrame(all_jobs[:30])[["职位", "公司", "来源", "链接"]]
    today = datetime.now().strftime("%Y-%m-%d")
    md_table = df.to_markdown(index=False)
    
    start_tag, end_tag = "", ""
    new_block = f"{start_tag}\n\n### 📅 更新时间: {today}\n\n{md_table}\n\n{end_tag}"

    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 核心修复：如果发现有多个重复标签或匹配失败，直接重构内容
        pattern = re.compile(f"{re.escape(start_tag)}.*?{re.escape(end_tag)}", re.DOTALL)
        
        if start_tag in content and end_tag in content:
            # 正常替换：把旧的所有内容（不管几百行）全部抹掉
            updated_content = pattern.sub(new_block, content)
        else:
            # 兜底：如果标签坏了，直接重写整个 README
            updated_content = f"# 远程职位监控\n\n{new_block}"
            
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(updated_content)
    
    # 同时更新 Excel 备份
    df.to_excel("remote_jobs_list.xlsx", index=False)
    print(f"✅ 成功清理并更新了 {len(df)} 条职位")

if __name__ == "__main__":
    data = scrape_wwr() + scrape_remote_ok()
    save_and_update(data)
