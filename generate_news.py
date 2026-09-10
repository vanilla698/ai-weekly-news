#!/usr/bin/env python3
"""
generate_news.py — 抓取 + AI 整理 + 渲染 周报
每次运行自动从 arXiv + GitHub 抓最新素材，调用 LLM 整理为 7 个模块的周报
"""
import json
import os
import re
import requests
from datetime import datetime, timedelta

# ========== 配置 ==========
OUTPUT_DIR = "news"
JSON_FILE = "news_data.json"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-c58a295530e6456daa4a8b9119d57697")
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


# ========== 1. 数据抓取 ==========
def fetch_arxiv(category="cs.AI", max_results=8):
    """arXiv 抓取最新论文"""
    url = f"http://export.arxiv.org/api/query?search_query=cat:{category}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"[WARN] arxiv {category}: {e}")
        return []
    papers = []
    entries = re.findall(r"<entry>(.*?)</entry>", resp.text, re.DOTALL)
    for entry in entries:
        title = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        summary = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        link = re.search(r"<id>(.*?)</id>", entry)
        authors = re.findall(r"<author>\s*<name>(.*?)</name>", entry)
        if title and link:
            papers.append({
                "title": re.sub(r"\s+", " ", title.group(1)).strip(),
                "summary": re.sub(r"\s+", " ", summary.group(1)).strip()[:300] if summary else "",
                "link": link.group(1).strip(),
                "authors": authors[:3],
            })
    return papers


def fetch_github_trending():
    """GitHub Trending（按 star 数 + AI 标签）"""
    seven_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    url = f"https://api.github.com/search/repositories?q=stars:>500+pushed:>{seven_days_ago}+topic:ai-agent&sort=stars&order=desc&per_page=10"
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "ai-weekly-bot"})
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception as e:
        print(f"[WARN] github: {e}")
        return []
    return [{
        "name": item["full_name"],
        "description": (item.get("description") or "")[:200],
        "stars": item["stargazers_count"],
        "link": item["html_url"],
    } for item in items[:10]]


def fetch_all():
    """抓取所有数据源"""
    print("🔬 抓取 arXiv 论文...")
    papers_ai = fetch_arxiv("cs.AI", 8)
    papers_ro = fetch_arxiv("cs.RO", 6)
    papers_cl = fetch_arxiv("cs.CL", 6)
    print(f"  cs.AI: {len(papers_ai)} 篇, cs.RO: {len(papers_ro)} 篇, cs.CL: {len(papers_cl)} 篇")

    print("⭐ 抓取 GitHub Trending...")
    gh = fetch_github_trending()
    print(f"  github: {len(gh)} 个")

    return {
        "fetched_at": datetime.now().isoformat(),
        "papers_ai": papers_ai,
        "papers_ro": papers_ro,
        "papers_cl": papers_cl,
        "github": gh,
    }


# ========== 2. AI 整理 ==========
PROMPT_TEMPLATE = """你是一个专业的 AI 与汽车科技情报编辑。基于以下本周抓取的原始素材，整理出一期周报。

【素材一：arXiv cs.AI 最新论文】
{papers_ai}

【素材二：arXiv cs.RO 机器人】
{papers_ro}

【素材三：arXiv cs.CL 自然语言处理】
{papers_cl}

【素材四：GitHub 本周热门 AI 项目】
{github}

【输出要求】严格按 JSON 格式返回，不要包含任何额外文字或 markdown 代码块标记。

{{
  "key_points": ["4 条本周要点，每条不超过 35 字，含 emoji 开头"],
  "ai_news": [
    {{"title": "新闻标题（中文翻译）", "summary": "30-60 字摘要", "link": "https://原始论文或项目链接", "source": "来源名如 arXiv/GitHub/HuggingFace"}}
  ],
  "auto_tech": [
    {{"title": "汽车科技标题", "summary": "30-60 字", "link": "https://...", "source": "来源"}}
  ],
  "leadership": [
    {{"title": "人事变动标题", "summary": "30-60 字", "link": "https://...", "source": "来源"}}
  ],
  "auto_ai": [
    {{"title": "汽车 AI 技术标题", "summary": "30-60 字", "link": "https://...", "source": "来源"}}
  ],
  "papers": [
    {{"title": "论文中文标题", "id": "arxiv_id", "authors": "作者", "summary": "30-60 字摘要"}}
  ],
  "github": [
    {{"name": "owner/repo", "stars": "星数", "summary": "30-60 字简介", "link": "https://github链接"}}
  ],
  "ai_deep": [
    {{"title": "深度评论标题", "summary": "30-60 字", "link": "https://...", "source": "来源"}}
  ],
  "summary": [
    {{"title": "本周总结小标题（5-15 字）", "content": "20-40 字总结", "color": "gold 或 green 或 purple"}}
  ]
}}

注意：
- ai_news 5 条、auto_tech 4 条、leadership 2 条、auto_ai 3 条、papers 5 条、github 5 条、ai_deep 3 条、summary 5 条
- 总结是本周要点提炼，不是新闻堆砌
- 所有 link 必须从素材中提取，真实有效
- 当素材不足时，对应模块可以用 arXiv 或 GitHub 项目填充
"""


def call_llm(data):
    """调用 DeepSeek API 整理为周报 JSON"""
    papers_ai_text = "\n".join([f"- {p['title']}\n  摘要: {p['summary'][:150]}\n  链接: {p['link']}" for p in data["papers_ai"]])
    papers_ro_text = "\n".join([f"- {p['title']}\n  链接: {p['link']}" for p in data["papers_ro"]])
    papers_cl_text = "\n".join([f"- {p['title']}\n  链接: {p['link']}" for p in data["papers_cl"]])
    github_text = "\n".join([f"- {g['name']} ({g['stars']} stars)\n  {g['description']}\n  链接: {g['link']}" for g in data["github"]])

    prompt = PROMPT_TEMPLATE.format(
        papers_ai=papers_ai_text or "（无数据）",
        papers_ro=papers_ro_text or "（无数据）",
        papers_cl=papers_cl_text or "（无数据）",
        github=github_text or "（无数据）",
    )

    if not DEEPSEEK_API_KEY:
        print("[WARN] DEEPSEEK_API_KEY 未配置，使用素材直接生成")
        return build_fallback(data)

    print("🤖 调用 DeepSeek AI 整理周报...")
    try:
        resp = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一个专业的科技情报编辑，严格按要求返回 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 4000,
            },
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()
        content = result["choices"][0]["message"]["content"]
        # 提取 JSON（兼容 AI 返回带 markdown 标记的情况）
        content = re.sub(r"^```json\s*", "", content.strip())
        content = re.sub(r"\s*```$", "", content)
        return json.loads(content)
    except Exception as e:
        print(f"[WARN] AI 整理失败: {e}")
        return build_fallback(data)


def build_fallback(data):
    """AI 调用失败时，从素材直接拼接"""
    papers_combined = (data["papers_ai"] + data["papers_ro"] + data["papers_cl"])[:7]
    return {
        "key_points": [
            f"🤖 本周 arXiv AI 论文 {len(data['papers_ai'])} 篇新发布",
            f"⭐ GitHub AI 项目 {len(data['github'])} 个热门",
            f"📡 数据自动抓取于 {datetime.now().strftime('%Y-%m-%d')}",
            f"🔬 机器人方向 {len(data['papers_ro'])} 篇新研究",
        ],
        "ai_news": [
            {
                "title": p["title"],
                "summary": p["summary"][:80] or "新研究发布",
                "link": p["link"],
                "source": "arXiv",
            } for p in data["papers_ai"][:5]
        ],
        "auto_tech": [
            {
                "title": p["title"],
                "summary": p["summary"][:80] or "机器人研究新进展",
                "link": p["link"],
                "source": "arXiv cs.RO",
            } for p in data["papers_ro"][:4]
        ],
        "leadership": [
            {
                "title": "本周车企人事动态",
                "summary": "数据源未覆盖，请关注专业汽车媒体",
                "link": "https://www.163.com/auto",
                "source": "网易汽车",
            }
        ],
        "auto_ai": [
            {
                "title": p["title"],
                "summary": p["summary"][:80] or "NLP 新研究",
                "link": p["link"],
                "source": "arXiv cs.CL",
            } for p in data["papers_cl"][:3]
        ],
        "papers": [
            {
                "title": p["title"],
                "id": p["link"].split("/")[-1] if "/" in p["link"] else "0000.00000",
                "authors": ", ".join(p["authors"]),
                "summary": p["summary"][:100],
            } for p in papers_combined[:5]
        ],
        "github": [
            {
                "name": g["name"],
                "stars": str(g["stars"]),
                "summary": g["description"] or "AI 项目",
                "link": g["link"],
            } for g in data["github"][:5]
        ],
        "ai_deep": [
            {
                "title": "本周 AI 领域观察",
                "summary": f"arXiv 收录 {len(data['papers_ai']) + len(data['papers_ro']) + len(data['papers_cl'])} 篇新论文",
                "link": "https://arxiv.org",
                "source": "arXiv",
            }
        ],
        "summary": [
            {"title": "AI 论文持续高产", "content": f"本周 arXiv 三大类共 {len(data['papers_ai']) + len(data['papers_ro']) + len(data['papers_cl'])} 篇新论文", "color": "gold"},
            {"title": "GitHub AI 项目活跃", "content": f"{len(data['github'])} 个 AI 项目持续获得关注", "color": "green"},
            {"title": "机器人方向研究密集", "content": f"cs.RO 收录 {len(data['papers_ro'])} 篇新论文", "color": "purple"},
        ],
    }


# ========== 3. HTML 渲染（保持原样）==========
def esc(s):
    if not s:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def stories_html(items):
    return "".join(
        '<div class="story">'
        f'<a class="link-title" href="{esc(item.get("link", "#"))}" target="_blank">{esc(item.get("title", ""))}</a>'
        f'<div class="story-summary">{esc(item.get("summary", ""))}</div>'
        f'<div class="story-meta"><a href="{esc(item.get("link", "#"))}" target="_blank">{esc(item.get("source", "链接"))} →</a></div>'
        '</div>'
        for item in items or []
    )


def hbox_html(title, content, color):
    return f'<div class="hbox {color}"><strong>{esc(title)}</strong>{content}</div>'


def paper_html(papers):
    return "".join(
        '<div class="paper-item">'
        f'<a class="paper-link" href="https://arxiv.org/abs/{p.get("id", "")}" target="_blank">{esc(p.get("title", ""))}</a>'
        f'<div class="paper-meta">{esc(p.get("authors", ""))} · arXiv:{esc(p.get("id", ""))}</div>'
        f'<div class="paper-summary">{esc(p.get("summary", ""))}</div>'
        '</div>'
        for p in papers or []
    )


def gh_html(ghs):
    return "".join(
        '<div class="github-item">'
        f'<div class="gh-stars">&#9733; {esc(g.get("name", ""))} — {esc(g.get("stars", ""))} stars</div>'
        f'<a class="gh-link" href="{esc(g.get("link", "#"))}" target="_blank">{esc(g.get("name", ""))}</a>'
        f'<div class="gh-summary">{esc(g.get("summary", ""))}</div>'
        '</div>'
        for g in ghs or []
    )


def build_html(data, archive_filename):
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    date_str = today.strftime("%Y年%-m月%-d日")
    kp_items = "".join(f'<div class="kp-item"><strong>{esc(k)}</strong></div>' for k in data.get("key_points", []))
    summary_blocks = "".join(
        hbox_html(s["title"], esc(s["content"]), s.get("color", "gold"))
        for s in data.get("summary", [])
    )
    leadership_blocks = "".join(
        hbox_html(
            item.get("title", ""),
            f'{esc(item.get("summary", ""))}<div class="src"><a href="{esc(item.get("link", "#"))}" target="_blank">来源：{esc(item.get("source", "链接"))} →</a></div>',
            "gold",
        )
        for item in data.get("leadership", [])
    )

    css = """
:root{--ink:#111;--ink-mid:#3a3a3a;--ink-light:#666;--ink-faint:#999;--rule:#222;--rule-light:#ddd;--accent:#c0392b;--accent-blue:#1a3a5c;--accent-gold:#8b6914;--accent-green:#1a5c2a;--accent-purple:#5c1a5c;--paper:#faf9f6;--paper-dark:#ede9e0;}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Noto Sans SC',sans-serif;background:var(--paper);color:var(--ink);font-size:13px;line-height:1.5;}
#root{width:90vw;margin:0 auto;}
.masthead{border-top:4px solid var(--ink);border-bottom:2px solid var(--ink);padding:6px 0 5px;margin-bottom:8px;display:flex;align-items:center;}
.mh-left{font-size:10px;color:var(--ink-light);line-height:1.8;white-space:nowrap;}
.mh-center{flex:1;text-align:center;}
.mh-center h1{font-family:'Noto Serif SC',serif;font-size:clamp(20px,3.5vw,38px);font-weight:900;letter-spacing:.18em;line-height:1.1;}
.mh-center .sub{font-size:clamp(9px,1vw,11px);letter-spacing:.25em;color:var(--ink-light);margin-top:2px;}
.mh-right{font-size:10px;color:var(--ink-light);line-height:1.8;text-align:right;white-space:nowrap;}
.kp-bar{display:flex;gap:0;border:1.5px solid var(--ink);margin-bottom:6px;flex-wrap:wrap;}
.kp-item{flex:1;min-width:180px;padding:7px 10px;border-right:1.5px solid var(--ink);font-size:11.5px;line-height:1.5;color:var(--ink-mid);}
.kp-item:last-child{border-right:none;}
.kp-item strong{color:var(--ink);font-size:12px;display:block;}
.sec-hdr{display:flex;align-items:center;gap:8px;margin:8px 0 5px;}
.sec-num{font-family:'Noto Serif SC',serif;font-size:11px;font-weight:700;color:#fff;background:var(--ink);padding:1px 5px;white-space:nowrap;}
.sec-num.blue{background:var(--accent-blue);}.sec-num.gold{background:var(--accent-gold);}.sec-num.green{background:var(--accent-green);}.sec-num.purple{background:var(--accent-purple);}.sec-num.accent{background:var(--accent);}
.sec-rule{flex:1;height:1.5px;}
.sec-title{font-family:'Noto Serif SC',serif;font-size:clamp(13px,1.8vw,16px);font-weight:700;white-space:nowrap;letter-spacing:.08em;}
.sec-title.accent{color:var(--accent);}.sec-title.blue{color:var(--accent-blue);}.sec-title.gold{color:var(--accent-gold);}.sec-title.green{color:var(--accent-green);}.sec-title.purple{color:var(--accent-purple);}
.main-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0;align-items:start;}
.col{display:flex;flex-direction:column;gap:0;}
.col-left{border-right:1px solid var(--rule-light);padding-right:10px;}
.col-mid{border-right:1px solid var(--rule-light);padding:0 10px;}
.col-right{padding-left:10px;}
.story{padding:5px 0;border-bottom:1px dashed var(--rule-light);}
.story:last-child{border-bottom:none;}
a.link-title{font-family:'Noto Serif SC',serif;font-size:13px;font-weight:700;color:var(--ink);text-decoration:none;display:block;line-height:1.4;}
a.link-title:hover{color:var(--accent);}
.story-summary{font-size:11.5px;color:var(--ink-mid);line-height:1.55;margin-top:3px;}
.story-meta{font-size:10px;color:var(--accent);margin-top:3px;font-weight:500;}
.story-meta a{color:var(--accent);text-decoration:none;}
.story-meta a:hover{text-decoration:underline;}
.hbox{border-top:2.5px solid var(--accent);background:var(--paper-dark);padding:6px 9px;margin:5px 0;font-size:11.5px;line-height:1.6;color:var(--ink-mid);}
.hbox.blue{border-color:var(--accent-blue);}.hbox.gold{border-color:var(--accent-gold);}.hbox.green{border-color:var(--accent-green);}.hbox.purple{border-color:var(--accent-purple);}
.hbox strong{color:var(--ink);font-size:12.5px;display:block;margin-bottom:2px;font-family:'Noto Serif SC',serif;}
.hbox .src{font-size:10px;color:var(--ink-faint);margin-top:3px;}.hbox .src a{color:var(--accent-gold);text-decoration:none;}.hbox .src a:hover{text-decoration:underline;}
.paper-item,.github-item{padding:5px 0;border-bottom:1px dashed var(--rule-light);}
.paper-item:last-child,.github-item:last-child{border-bottom:none;}
a.paper-link{font-family:'Noto Serif SC',serif;font-size:12.5px;font-weight:700;color:var(--ink);text-decoration:none;display:block;line-height:1.4;margin-bottom:2px;}
a.paper-link:hover{color:var(--accent-purple);}
.paper-meta{font-size:9.5px;color:var(--accent-purple);font-weight:600;margin-bottom:2px;}
.paper-summary{font-size:11px;color:var(--ink-mid);line-height:1.55;}
.gh-stars{font-size:9.5px;color:var(--accent-purple);font-weight:700;margin-bottom:2px;}
a.gh-link{font-size:12px;font-weight:700;color:var(--ink);text-decoration:none;display:block;margin-bottom:2px;}
a.gh-link:hover{color:var(--accent-purple);}
.gh-summary{font-size:11px;color:var(--ink-mid);line-height:1.55;}
.multi-col{columns:2;column-gap:16px;}
.multi-col .story,.multi-col .paper-item,.multi-col .github-item,.multi-col .hbox{break-inside:avoid;}
.footer{border-top:2px solid var(--ink);margin-top:8px;padding:5px 0;font-size:10px;color:var(--ink-faint);display:flex;justify-content:space-between;letter-spacing:.05em;}
@media(max-width:900px){.main-grid{grid-template-columns:1fr 1fr;}.col-right{border-left:1px solid var(--rule-light);padding-left:10px;}.multi-col{columns:1;}}
@media(max-width:600px){.main-grid{grid-template-columns:1fr;}.col-left,.col-mid{border-right:none;padding-right:0;}.col-right{border-left:none;padding-left:0;}}
"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI汽车科技每周情报 | {date_str} 第{issue}期</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700;900&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<div id="root">
<header class="masthead">
<div class="mh-left">{date_str} · 星期三<br>第 {issue} 期 · 总第 {issue+484} 期<br>归档：{archive_filename}</div>
<div class="mh-center"><h1>AI · 汽车科技每周情报</h1><div class="sub">AI科技 · 车企动态 · 汽车AI技术 · 技术论文 · 行业总结</div></div>
<div class="mh-right">关键词：情报<br>订阅：钉钉群推送</div>
</header>
<div class="kp-bar">{kp_items}</div>
<div class="main-grid">
<div class="col col-left">
<div class="sec-hdr"><span class="sec-num accent">01</span><div class="sec-rule" style="background:var(--accent);"></div><span class="sec-title accent">AI 圈 新 闻</span></div>
<div class="multi-col">{stories_html(data.get("ai_news", []))}</div>
<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num accent">06</span><div class="sec-rule" style="background:var(--accent);"></div><span class="sec-title accent">AI 圈 深 度</span></div>
<div class="multi-col">{stories_html(data.get("ai_deep", []))}</div>
<hbox-placeholder style="display:none"></hbox-placeholder>
<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num gold">07</span><div class="sec-rule" style="background:var(--accent-gold);"></div><span class="sec-title gold">本 周 总 结</span></div>
<div class="multi-col">{summary_blocks}</div>
</div>
<div class="col col-mid">
<div class="sec-hdr"><span class="sec-num blue">02</span><div class="sec-rule" style="background:var(--accent-blue);"></div><span class="sec-title blue">车 企 科 技</span></div>
<div class="multi-col">{stories_html(data.get("auto_tech", []))}</div>
<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num gold">03</span><div class="sec-rule" style="background:var(--accent-gold);"></div><span class="sec-title gold">领 导 变 动</span></div>
<div class="multi-col">{leadership_blocks}</div>
<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num green">04</span><div class="sec-rule" style="background:var(--accent-green);"></div><span class="sec-title green">汽 车 AI 技 术</span></div>
<div class="multi-col">{stories_html(data.get("auto_ai", []))}</div>
</div>
<div class="col col-right">
<div class="sec-hdr"><span class="sec-num purple">05</span><div class="sec-rule" style="background:var(--accent-purple);"></div><span class="sec-title purple">技 术 论 文</span></div>
<div class="multi-col">{paper_html(data.get("papers", []))}</div>
<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num purple">&#9733;</span><div class="sec-rule" style="background:var(--accent-purple);"></div><span class="sec-title purple">GitHub 开 源</span></div>
<div class="multi-col">{gh_html(data.get("github", []))}</div>
</div>
</div>
<footer class="footer"><span>📡 本情报由 Mavis 每周自动抓取整理</span><span>每周三 08:00 定时推送至钉钉群</span><span>第 {issue} 期 · {date_str}</span></footer>
</div>
</body>
</html>"""


# ========== 4. 主流程 ==========
def main():
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    week_tag = today.strftime("%Y%m%d")
    archive_filename = f"{week_tag}-issue{issue}.html"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    archive_path = os.path.join(OUTPUT_DIR, archive_filename)

    # Step 1: 抓取
    raw = fetch_all()
    print(f"\n📦 共抓取: AI 论文 {len(raw['papers_ai'])} 篇, RO 论文 {len(raw['papers_ro'])} 篇, CL 论文 {len(raw['papers_cl'])} 篇, GitHub {len(raw['github'])} 个")

    # 保存原始数据
    raw_path = os.path.join(OUTPUT_DIR, f"raw-{week_tag}.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)
    print(f"💾 原始数据: {raw_path}")

    # Step 2: AI 整理
    news_data = call_llm(raw)
    print(f"📰 AI 整理完成，模块数: {len(news_data)}")

    # 保存周报 JSON
    json_path = os.path.join(OUTPUT_DIR, f"data-{week_tag}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    print(f"💾 周报数据: {json_path}")

    # Step 3: 渲染
    html = build_html(news_data, archive_filename)
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(html)
    latest_path = os.path.join(OUTPUT_DIR, "latest.html")
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"📄 归档: {archive_path}")
    print(f"📄 最新: {latest_path}")
    print(f"\n✅ 第 {issue} 期生成完成")


if __name__ == "__main__":
    main()
