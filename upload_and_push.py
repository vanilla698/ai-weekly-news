#!/usr/bin/env python3
"""
upload_and_push.py — 把 HTML 发布到 GitHub Gist 并推送钉钉
GitHub Gist 永久免费，URL 稳定不变
"""
import os, sys, json, base64, requests
from datetime import datetime

HTML_FILE = "ai_auto_news_preview.html"
GITHUB_API = "https://api.github.com"
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")
TOKEN_GITHUB = os.environ.get("TOKEN_GITHUB", "")

def create_gist(filename, content):
    """创建公开 Gist，返回 URL"""
    if not TOKEN_GITHUB:
        print("[ERROR] TOKEN_GITHUB not set — add it to repo Secrets")
        sys.exit(1)
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    date_str = today.strftime("%Y%m%d")
    gist_name = f"ai-weekly-news-{date_str}-issue{issue}.html"

    headers = {
        "Authorization": f"token {TOKEN_GITHUB}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    payload = {
        "description": f"AI汽车科技每周情报 第{issue}期 | {date_str} | 每周三08:00自动推送",
        "public": True,
        "files": {
            gist_name: {
                "content": content,
            }
        },
    }
    resp = requests.post(
        f"{GITHUB_API}/gists",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    # raw URL 指向 HTML 文件
    gist_url = data["files"][gist_name]["raw_url"].replace("gist.githubusercontent.com", "gist.githubusercontent.com")
    html_url = data["html_url"]
    print(f"[OK] Gist created: {html_url}")
    print(f"[OK] Raw HTML: {gist_url}")
    return gist_url, html_url

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
    with open(HTML_FILE, encoding="utf-8") as f:
        content = f.read()
    # Gist raw URL 直接作为公开访问地址
    url, gist_url = create_gist(HTML_FILE, content)
    send_dingtalk(url)
    print(f"=== Done! URL: {url} ===")

if __name__ == "__main__":
    main()
