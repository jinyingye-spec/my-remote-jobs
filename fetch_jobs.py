import feedparser import datetime import re import pandas as pd import os import requests import json

RSS_SOURCES = { "We Work Remotely": "", "Working Nomads": "", "DailyRemote": "", "JustRemote": "", "Upwork (Global)": "", "Freelancer": "" }

def clean_text(text): if not text: return "" return re.sub('<[^\<]+?>', '', text)

def fetch_remotive(): jobs = [] try: response = requests.get("") if response.status_code == 200: data = response.json() for item in data.get('jobs', []): jobs.append({ "platform": "Remotive", "priority": "⭐ High" if "anywhere" in item.get('candidate_required_location', '').lower() else "Normal", "title": item.get('title'), "location": item.get('candidate_required_location', 'Remote'), "salary": item.get('salary', 'Check website'), "date": item.get('publication_date', '')[:10], "link": item.get('url') }) except: pass return jobs

def fetch_and_save(): now = datetime.datetime.now() + datetime.timedelta(hours=8) sheet_name = now.strftime('%Y-%m-%d') excel_file = "remote_jobs_list.xlsx" all_data = []

if name == "main": fetch_and_save()
