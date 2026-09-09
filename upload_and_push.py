#!/usr/bin/env python3
import os, sys, requests
from datetime import datetime

HTML_FILE = "ai_auto_news_preview.html"
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")
GH_TOKEN = os.environ.get("GH_TOKEN", "")

def create_gist():
    if not GH_TOKEN:
        print("[ERROR] GH_TOKEN not set in Secrets")
        sys.exit(1)
    with open(HTML_FILE, encoding="utf-8") as f:
        content = f.read()
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    gist_name = f"ai-weekly-news-{today.strftime('%Y%m%d')}-i{issue}.html"
    resp = requests.post(
        "https://api.github.com/gists",
        headers={
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={
            "description": f"AI汽车科技每周情报 第{issue}期",
            "public": True,
            "files": {gist_name: {"content": content}},
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"[OK] Gist: {data['html_url']}")
    return data["files"][gist_name]["raw_url"]

def send_dingtalk(url):
    if not DINGTALK_WEBHOOK:
        print("[SKIP] DINGTALK_WEBHOOK not set")
        return
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    body = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"AI汽车科技每周情报 | 第{issue}期",
            "text": (
                f"## 📡 AI汽车科技每周情报 | 第{issue}期\n\n"
                f"📅 {today.strftime('%Y年%m月%d日')} · 星期{['一','二','三','四','五','六','日'][today.weekday()]}\n\n"
                f"👉 [点击查看带样式完整情报]({url})\n\n"
                f"🔔 每周三 08:00 自动推送\n"
            ),
        },
    }
    r = requests.post(DINGTALK_WEBHOOK, json=body, timeout=15)
    result = r.json()
    print("[OK] DingTalk sent" if result.get("errcode") == 0 else f"[ERROR] {result}")

def main():
    print(f"=== AI汽车科技每周情报 · 发布 ===")
    url = create_gist()
    send_dingtalk(url)
    print(f"=== Done: {url} ===")

if __name__ == "__main__":
    main()
