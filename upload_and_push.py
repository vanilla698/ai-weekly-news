#!/usr/bin/env python3
"""
upload_and_push.py — 推送钉钉消息，链接指向 GitHub Pages 历史归档列表页
"""
import os, requests
from datetime import datetime

DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")
GITHUB_PAGES_BASE = "https://vanilla698.github.io/ai-weekly-news"


def send_dingtalk():
    if not DINGTALK_WEBHOOK:
        print("[SKIP] DINGTALK_WEBHOOK not set")
        return
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    date_str = today.strftime("%Y年%m月%d日")
    wk = ["一","二","三","四","五","六","日"][today.weekday()]

    index_url = f"{GITHUB_PAGES_BASE}/news/index.html"
    latest_url = f"{GITHUB_PAGES_BASE}/news/latest.html"

    body = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"AI汽车科技每周情报 | 第{issue}期",
            "text": (
                f"## 📡 AI汽车科技每周情报 | 第{issue}期\n\n"
                f"📅 {date_str} · 星期{wk}\n\n"
                f"🔔 每周三 08:00 自动推送 · 数据全网实时抓取\n\n"
                f"---\n\n"
                f"👉 [点击查看本期完整情报]({latest_url})\n\n"
                f"📋 [查看所有历史归档列表]({index_url})\n\n"
                f"---\n\n"
                f"🔔 由 GitHub Actions 自动驱动 · 数据源：arXiv + HuggingFace + 7 大 RSS\n"
            ),
        },
    }
    r = requests.post(DINGTALK_WEBHOOK, json=body, timeout=15)
    result = r.json()
    if result.get("errcode") == 0:
        print(f"[OK] DingTalk sent · issue #{issue}")
    else:
        print(f"[ERROR] {result}")


if __name__ == "__main__":
    print(f"=== AI汽车科技每周情报 · 发布 ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    send_dingtalk()
