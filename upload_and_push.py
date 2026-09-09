#!/usr/bin/env python3
"""
upload_and_push.py — 用 gh CLI 创建 Gist 并推送钉钉
"""
import os, sys, subprocess, requests
from datetime import datetime

HTML_FILE = "ai_auto_news_preview.html"
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "") 

def create_gist(filename):
    """用 gh CLI 创建公开 Gist"""
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    date_str = today.strftime("%Y%m%d")
    desc = f"AI汽车科技每周情报 第{issue}期 {date_str}"
    result = subprocess.run(
        ["gh", "gist", "create", filename, "--desc", desc, "--public"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"[ERROR] gh gist failed: {result.stderr}")
        sys.exit(1)
    gist_url = result.stdout.strip()
    print(f"[OK] Gist: {gist_url}")
    # raw URL 用于钉钉打开时直接渲染 HTML
    raw_url = gist_url.replace("https://gist.github.com/", "https://gist.githubusercontent.com/") + "/raw/" + filename
    print(f"[OK] Raw: {raw_url}")
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
    url = create_gist(HTML_FILE)
    send_dingtalk(url)
    print(f"=== Done! URL: {url} ===")

if __name__ == "__main__":
    main()
