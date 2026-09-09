#!/usr/bin/env python3
"""
upload_and_push.py — 发布到 GitHub Gist 并推送钉钉
"""
import os, sys, requests
from datetime import datetime

HTML_FILE = "ai_auto_news_preview.html"
GITHUB_API = "https://api.github.com"
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")
GITHUB_TOKEN = os.environ.get("TOKEN_GITHUB", "")

def create_gist(filename, content):
    if not GITHUB_TOKEN:
        print("[ERROR] TOKEN_GITHUB not set")
        sys.exit(1)
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    date_str = today.strftime("%Y%m%d")
    gist_name = f"ai-weekly-news-{date_str}-i{issue}.html"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "description": f"AI汽车科技每周情报 第{issue}期 {date_str}",
        "public": True,
        "files": {gist_name: {"content": content}},
    }
    resp = requests.post(
        f"{GITHUB_API}/gists",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    gist_url = data["html_url"]
    raw_url = data["files"][gist_name]["raw_url"]
    print(f"[OK] Gist: {gist_url}")
    return raw_url

def send_dingtalk(url):
    if not DINGTALK_WEBHOOK:
        print("[SKIP] DINGTALK_WEBHOOK not set")
        return
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    date_str = today.strftime("%Y年%m月%d日")
    wk = ["一","二","三","四","五","六","日"][today.weekday()]
    body = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"AI汽车科技每周情报 | 第{issue}期",
            "text": (
                f"## 📡 AI汽车科技每周情报 | 第{issue}期\n\n"
                f"📅 {date_str} · 星期{wk}\n\n"
                f"> 大模型竞争 · 具身智能 · 车企人事 · 汽车AI技术 · 技术论文与开源生态\n\n"
                f"👉 [点击查看完整情报]({url})\n\n"
                f"---\n\n"
                f"🔔 每周三 08:00 自动推送 · GitHub Actions 驱动\n"
            ),
        },
    }
    resp = requests.post(DINGTALK_WEBHOOK, json=body, timeout=15)
    result = resp.json()
    if result.get("errcode") != 0:
        print(f"[ERROR] DingTalk: {result}")
    else:
        print("[OK] DingTalk message sent")

def main():
    print(f"=== AI汽车科技每周情报 · 发布 ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if not os.path.exists(HTML_FILE):
        print(f"[ERROR] {HTML_FILE} not found")
        sys.exit(1)
    with open(HTML_FILE, encoding="utf-8") as f:
        content = f.read()
    url = create_gist(HTML_FILE, content)
    send_dingtalk(url)
    print(f"=== Done! URL: {url} ===")

if __name__ == "__main__":
    main()
