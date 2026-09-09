#!/usr/bin/env python3
"""
upload_and_push.py — 推送钉钉图文消息
直接从仓库 README 拿最新 HTML 预览链接，再附带完整新闻文字版到钉钉
"""
import os, requests
from datetime import datetime

DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")

def get_html_url():
    """GitHub 仓库里 HTML 文件的固定链接（每次 push 都会更新）"""
    return "https://github.com/vanilla698/ai-weekly-news/blob/main/ai_auto_news_preview.html"

def send_dingtalk():
    if not DINGTALK_WEBHOOK:
        print("[SKIP] DINGTALK_WEBHOOK not set")
        return
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    date_str = today.strftime("%Y年%m月%d日")
    wk = ["一","二","三","四","五","六","日"][today.weekday()]
    html_url = get_html_url()
    body = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"AI汽车科技每周情报 | 第{issue}期",
            "text": (
                f"## 📡 AI汽车科技每周情报 | 第{issue}期\n\n"
                f"📅 {date_str} · 星期{wk}\n\n"
                f"### 四大看点\n"
                f"🤖 **Claude Fable 5.1**：成本↓25%，Agent任务成本最高↓45%\n"
                f"💰 **英伟达收购HF**：129亿美元，AI最大收购案\n"
                f"🔔 **车企密集换帅**：李书福辞任吉利董事会主席\n"
                f"🤝 **具身智能爆发**：小鹏机器人估值63亿美元\n\n"
                f"---\n\n"
                f"📰 **完整版（含 7 篇论文 + 5 个开源项目）**\n"
                f"👉 [点击查看]({html_url})\n\n"
                f"---\n\n"
                f"🔔 每周三 08:00 自动推送 · GitHub Actions 驱动\n"
                f"📂 历史档案：https://github.com/vanilla698/ai-weekly-news/tree/main\n"
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
