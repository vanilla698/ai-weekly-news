#!/usr/bin/env python3
"""
upload_and_push.py — 推送钉钉消息，HTML 通过 GitHub 原始文件 URL 访问
"""
import os, sys, requests
from datetime import datetime

HTML_FILE = "ai_auto_news_preview.html"
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "vanilla698/ai-weekly-news")

def get_html_url():
    """GitHub raw 文件永久 URL"""
    branch = "main"
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{branch}/{HTML_FILE}"

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
    url = get_html_url()
    print(f"[INFO] HTML URL: {url}")
    send_dingtalk(url)
    print(f"=== Done! ===")

if __name__ == "__main__":
    main()
