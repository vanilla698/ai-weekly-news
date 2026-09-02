#!/usr/bin/env python3
"""
upload_and_push.py — 上传 HTML 并推送钉钉
"""
import os, sys, requests
from datetime import datetime

HTML_FILE = "ai_auto_news_preview.html"
# 免费文件托管，永久存储
UPLOAD_URL = "https://0x0.st"
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")

def upload_file(path):
    if not os.path.exists(path):
        print(f"[ERROR] File not found: {path}")
        sys.exit(1)
    print(f"[INFO] Uploading to 0x0.st...")
    with open(path, "rb") as f:
        resp = requests.post(UPLOAD_URL, files={"file": (path, f)}, timeout=120)
        resp.raise_for_status()
    url = resp.text.strip()
    if not url.startswith("http"):
        print(f"[ERROR] 0x0.st returned: {url}")
        sys.exit(1)
    print(f"[OK] Uploaded: {url}")
    return url

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
        print(f"[ERROR] {HTML_FILE} not found — run generate_news.py first")
        sys.exit(1)
    url = upload_file(HTML_FILE)
    send_dingtalk(url)
    print(f"=== Done! URL: {url} ===")

if __name__ == "__main__":
    main()
