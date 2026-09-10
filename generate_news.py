#!/usr/bin/env python3
"""
generate_news.py — 抓取 + AI 整理 + 渲染 AI 汽车科技周报
数据源：arXiv + GitHub + 车企/AI巨头官网 RSS + HF 模型 + HN
"""
import json
import os
import re
import sys
import requests
from datetime import datetime, timedelta

# 让脚本能找到 fetch_news_sources
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_news_sources import (
    fetch_rss, fetch_hn, fetch_hf_models,
    AI_GIANT_RSS, AUTO_COMPANY_RSS, CN_TECH_RSS,
)

# ========== 配置 ==========
OUTPUT_DIR = "news"
JSON_FILE = "news_data.json"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-c58a295530e6456daa4a8b9119d57697")
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


# ========== 1. arXiv 抓取 ==========
def fetch_arxiv(category="cs.AI", max_results=8):
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


# ========== 2. 抓取所有源 ==========
def fetch_all():
    print("🔬 抓取 arXiv 论文...")
    papers_ai = fetch_arxiv("cs.AI", 8)
    papers_ro = fetch_arxiv("cs.RO", 6)
    papers_cl = fetch_arxiv("cs.CL", 6)
    print(f"  cs.AI {len(papers_ai)} | cs.RO {len(papers_ro)} | cs.CL {len(papers_cl)}")

    print("🤖 抓取 AI 巨头官网...")
    ai_giants = []
    for name, url in AI_GIANT_RSS.items():
        ai_giants.extend(fetch_rss(url, name, max_items=3))

    print("🚗 抓取车企官网...")
    auto_companies = []
    for name, url in AUTO_COMPANY_RSS.items():
        auto_companies.extend(fetch_rss(url, name, max_items=3))

    print("📰 抓取中文科技媒体...")
    cn_tech = []
    for name, url in CN_TECH_RSS.items():
        cn_tech.extend(fetch_rss(url, name, max_items=3))

    print("💬 抓取 Hacker News...")
    hn = fetch_hn(max_items=8)

    print("🤗 抓取 HuggingFace 模型...")
    hf_models = fetch_hf_models(limit=15)

    return {
        "fetched_at": datetime.now().isoformat(),
        "papers_ai": papers_ai,
        "papers_ro": papers_ro,
        "papers_cl": papers_cl,
        "ai_giants": ai_giants,
        "auto_companies": auto_companies,
        "cn_tech": cn_tech,
        "hn": hn,
        "hf_models": hf_models,
    }


# ========== 3. AI 整理 ==========
PROMPT_TEMPLATE = """你是资深的 AI 与汽车科技情报编辑。基于以下本周抓取的原始素材，整理出一期情报周报。

## 素材列表

【1. arXiv cs.AI 最新论文】
{papers_ai}

【2. arXiv cs.RO 机器人】
{papers_ro}

【3. arXiv cs.CL 自然语言处理】
{papers_cl}

【4. AI 巨头官网新闻】
{ai_giants}

【5. 车企官网新闻】
{auto_companies}

【6. 中文科技媒体】
{cn_tech}

【7. Hacker News 高赞】
{hn}

【8. HuggingFace 热门模型】
{hf_models}

## 输出要求

严格按 JSON 格式返回，不要包含任何额外文字或 markdown 代码块标记：

{{
  "key_points": [
    "4 条本周要点，每条不超过 40 字，含 emoji 开头"
  ],
  "ai_news": [
    {{"title": "新闻标题（中文）", "summary": "30-60 字", "link": "https://...（必须从素材提取）", "source": "来源"}}
  ],
  "auto_tech": [
    {{"title": "汽车科技新闻（中文）", "summary": "30-60 字", "link": "https://...（必须从素材提取）", "source": "来源"}}
  ],
  "leadership": [
    {{"title": "车企人事变动", "summary": "30-60 字", "link": "https://...（必须从素材提取）", "source": "来源"}}
  ],
  "auto_ai": [
    {{"title": "汽车 AI 技术（中文）", "summary": "30-60 字", "link": "https://...（必须从素材提取）", "source": "来源"}}
  ],
  "papers": [
    {{"title": "论文中文标题", "id": "arxiv_id（仅数字部分）", "authors": "作者", "summary": "30-60 字"}}
  ],
  "github": [
    {{"name": "owner/repo", "stars": "星数", "summary": "30-60 字", "link": "https://github链接"}}
  ],
  "ai_deep": [
    {{"title": "深度评论（中文）", "summary": "30-60 字", "link": "https://...", "source": "来源"}}
  ],
  "models": [
    {{"model_id": "owner/repo", "pipeline": "任务类型", "downloads": "数字字符串如 1.2M", "likes": "数字", "summary": "30-50 字模型简介（中文翻译或描述）", "link": "https://huggingface.co/owner/repo"}}
  ],
  "summary": [
    {{"title": "本周总结小标题（5-15 字）", "content": "20-40 字总结", "color": "gold 或 green 或 purple"}}
  ]
}}

## 数量与配比
- key_points: 4 条
- ai_news: 5 条（来自素材 4、5、6 优先，HF/HN 补）
- auto_tech: 4 条（素材 5 优先，不足用素材 6 补）
- leadership: 2 条（素材 5 车企人事相关；不足时填 "本周暂无重大人事变动"）
- auto_ai: 3 条（素材 5 中 AI 主题，素材 2/3 中机器人/AI 也可）
- papers: 5 条（必须来自 arXiv 素材 1/2/3）
- github: 5 条（必须来自素材 4 中 HuggingFace 之外的 GitHub 热门）
- ai_deep: 3 条（深度评论，可基于素材 1/4/7）
- models: 5 条（必须来自素材 8 HuggingFace 模型）
- summary: 5 条

## 关键约束
1. **所有 link 必须从素材原文提取，真实有效**，严禁编造
2. 标题用中文，summary 简洁专业
3. 当某个模块素材不足时，对应模块用 arXiv / HF / HN 素材合理填充
4. summary 的 color 用 gold/green/purple 三色轮换
5. models 的 model_id / link / downloads / likes 必须严格沿用素材原文
6. 返回纯 JSON，不要 ```json 标记
"""


def call_llm(data):
    """调用 DeepSeek API 整理为周报 JSON"""
    def fmt(items, max_summary=100):
        return "\n".join([
            f"- {it.get('title', it.get('model_id', ''))}\n  摘要: {(it.get('summary','') or '')[:max_summary]}\n  链接: {it.get('link','')}\n  来源: {it.get('source','')}"
            for it in items
        ]) or "（无）"

    def fmt_models(models):
        return "\n".join([
            f"- {m.get('model_id','')} | pipeline: {m.get('pipeline','')} | downloads: {m.get('downloads',0)} | likes: {m.get('likes',0)} | {m.get('link','')}"
            for m in models
        ]) or "（无）"

    prompt = PROMPT_TEMPLATE.format(
        papers_ai=fmt(data["papers_ai"]),
        papers_ro=fmt(data["papers_ro"]),
        papers_cl=fmt(data["papers_cl"]),
        ai_giants=fmt(data["ai_giants"]),
        auto_companies=fmt(data["auto_companies"]),
        cn_tech=fmt(data["cn_tech"]),
        hn=fmt(data["hn"]),
        hf_models=fmt_models(data["hf_models"]),
    )

    if not DEEPSEEK_API_KEY:
        print("[WARN] DEEPSEEK_API_KEY 未配置")
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
                    {"role": "system", "content": "你是资深的科技情报编辑，严格按要求返回 JSON，禁止任何额外文字。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 6000,
            },
            timeout=180,
        )
        if resp.status_code != 200:
            print(f"[WARN] DeepSeek {resp.status_code}: {resp.text[:200]}")
            return build_fallback(data)
        result = resp.json()
        content = result["choices"][0]["message"]["content"]
        content = re.sub(r"^```json\s*", "", content.strip())
        content = re.sub(r"\s*```$", "", content)
        return json.loads(content)
    except Exception as e:
        print(f"[WARN] AI 整理失败: {e}")
        return build_fallback(data)


def build_fallback(data):
    """AI 调用失败时，从素材直接拼接"""
    papers_combined = (data["papers_ai"] + data["papers_ro"] + data["papers_cl"])[:7]
    news_combined = (data["ai_giants"] + data["cn_tech"] + data["hn"])[:10]
    return {
        "key_points": [
            f"🤖 AI 巨头官网 {len(data['ai_giants'])} 条新闻",
            f"🚗 车企动态 {len(data['auto_companies'])} 条更新",
            f"🤗 HuggingFace {len(data['hf_models'])} 个热门模型",
            f"📡 数据自动抓取于 {datetime.now().strftime('%Y-%m-%d')}",
        ],
        "ai_news": [
            {"title": n["title"][:60], "summary": (n.get("summary", "") or "")[:80], "link": n["link"], "source": n.get("source", "链接")}
            for n in news_combined[:5]
        ] or [{"title": "AI 资讯聚合", "summary": "本周 AI 领域持续活跃", "link": "https://openai.com", "source": "OpenAI"}],
        "auto_tech": [
            {"title": n["title"][:60], "summary": (n.get("summary", "") or "")[:80], "link": n["link"], "source": n.get("source", "链接")}
            for n in data["auto_companies"][:4]
        ] or [{"title": "车企科技动态", "summary": "本周车企密集发布新技术", "link": "https://www.press.bmwgroup.com/", "source": "BMW"}],
        "leadership": [
            {"title": "本周车企人事动态", "summary": "数据源未覆盖人事变动，请关注专业汽车媒体", "link": "https://www.163.com/auto/", "source": "网易汽车"}
        ] if not data["auto_companies"] else [
            {"title": data["auto_companies"][0]["title"][:60], "summary": (data["auto_companies"][0].get("summary") or "车企动态")[:80], "link": data["auto_companies"][0]["link"], "source": data["auto_companies"][0].get("source", "链接")}
        ],
        "auto_ai": [
            {"title": p["title"][:60], "summary": p.get("summary", "")[:80], "link": p["link"], "source": "arXiv cs.RO"}
            for p in data["papers_ro"][:3]
        ] or [{"title": "汽车 AI 技术", "summary": "汽车智能化加速", "link": "https://arxiv.org/list/cs.RO/recent", "source": "arXiv"}],
        "papers": [
            {"title": p["title"], "id": p["link"].split("/")[-1] if "/" in p["link"] else "0000.00000", "authors": ", ".join(p.get("authors", [])), "summary": p.get("summary", "")[:100]}
            for p in papers_combined[:5]
        ],
        "github": [
            {"name": m["title"], "stars": str(m.get("likes", 0)), "summary": m.get("summary", "")[:80], "link": m.get("link", "")}
            for m in data["hf_models"][:5]
        ],
        "ai_deep": [
            {"title": h["title"][:60], "summary": h.get("summary", "高赞讨论"), "link": h["link"], "source": h.get("source", "HN")}
            for h in data["hn"][:3]
        ],
        "models": [
            {
                "model_id": m.get("model_id", m.get("title", "")),
                "pipeline": m.get("pipeline", "通用"),
                "downloads": m.get("downloads_str", str(m.get("downloads", 0))),
                "likes": str(m.get("likes", 0)),
                "summary": m.get("summary", ""),
                "link": m.get("link", ""),
            }
            for m in data["hf_models"][:5]
        ],
        "summary": [
            {"title": "AI 巨头动态密集", "content": f"本周 OpenAI/Google/NVIDIA 等发布 {len(data['ai_giants'])} 条更新", "color": "gold"},
            {"title": "车企加速 AI 化", "content": f"车企官网 {len(data['auto_companies'])} 条新闻，AI 渗透加速", "color": "green"},
            {"title": "HF 模型热度高", "content": f"本周 {len(data['hf_models'])} 个热门模型在 HF 出圈", "color": "purple"},
            {"title": "中文科技媒体活跃", "content": f"爱范儿、极客公园等 {len(data['cn_tech'])} 条更新", "color": "gold"},
            {"title": "arXiv 研究持续", "content": f"本周 {len(data['papers_ai']) + len(data['papers_ro']) + len(data['papers_cl'])} 篇新论文", "color": "green"},
        ],
    }


# ========== 4. HTML 渲染 ==========
def esc(s):
    if s is None:
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
        f'<div class="gh-stars">&#9733; {esc(g.get("name", ""))} — {esc(g.get("stars", ""))}</div>'
        f'<a class="gh-link" href="{esc(g.get("link", "#"))}" target="_blank">{esc(g.get("name", ""))}</a>'
        f'<div class="gh-summary">{esc(g.get("summary", ""))}</div>'
        '</div>'
        for g in ghs or []
    )


def models_html(models):
    return "".join(
        '<div class="model-item">'
        f'<a class="model-name" href="{esc(m.get("link", "#"))}" target="_blank">{esc(m.get("model_id", m.get("title", "")))}</a>'
        f'<div class="model-meta">📥 {esc(m.get("downloads", ""))} · ⭐ {esc(m.get("likes", ""))} · 🏷️ {esc(m.get("pipeline", ""))}</div>'
        f'<div class="model-summary">{esc(m.get("summary", ""))}</div>'
        '</div>'
        for m in models or []
    )


def leadership_html(items):
    return "".join(
        hbox_html(
            item.get("title", ""),
            f'{esc(item.get("summary", ""))}<div class="src"><a href="{esc(item.get("link", "#"))}" target="_blank">来源：{esc(item.get("source", "链接"))} →</a></div>',
            "gold",
        )
        for item in items or []
    )


CSS = """
:root{--ink:#111;--ink-mid:#3a3a3a;--ink-light:#666;--ink-faint:#999;--rule:#222;--rule-light:#ddd;--accent:#c0392b;--accent-blue:#1a3a5c;--accent-gold:#8b6914;--accent-green:#1a5c2a;--accent-purple:#5c1a5c;--accent-orange:#a05a1c;--paper:#faf9f6;--paper-dark:#ede9e0;}
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
.sec-num.blue{background:var(--accent-blue);}.sec-num.gold{background:var(--accent-gold);}.sec-num.green{background:var(--accent-green);}.sec-num.purple{background:var(--accent-purple);}.sec-num.accent{background:var(--accent);}.sec-num.orange{background:var(--accent-orange);}
.sec-rule{flex:1;height:1.5px;}
.sec-title{font-family:'Noto Serif SC',serif;font-size:clamp(13px,1.8vw,16px);font-weight:700;white-space:nowrap;letter-spacing:.08em;}
.sec-title.accent{color:var(--accent);}.sec-title.blue{color:var(--accent-blue);}.sec-title.gold{color:var(--accent-gold);}.sec-title.green{color:var(--accent-green);}.sec-title.purple{color:var(--accent-purple);}.sec-title.orange{color:var(--accent-orange);}
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
.hbox.blue{border-color:var(--accent-blue);}.hbox.gold{border-color:var(--accent-gold);}.hbox.green{border-color:var(--accent-green);}.hbox.purple{border-color:var(--accent-purple);}.hbox.ink{border-color:var(--ink);}
.hbox strong{color:var(--ink);font-size:12.5px;display:block;margin-bottom:2px;font-family:'Noto Serif SC',serif;}
.hbox .src{font-size:10px;color:var(--ink-faint);margin-top:3px;}.hbox .src a{color:var(--accent-gold);text-decoration:none;}.hbox .src a:hover{text-decoration:underline;}
.paper-item,.github-item,.model-item{padding:5px 0;border-bottom:1px dashed var(--rule-light);}
.paper-item:last-child,.github-item:last-child,.model-item:last-child{border-bottom:none;}
a.paper-link{font-family:'Noto Serif SC',serif;font-size:12.5px;font-weight:700;color:var(--ink);text-decoration:none;display:block;line-height:1.4;margin-bottom:2px;}
a.paper-link:hover{color:var(--accent-purple);}
.paper-meta{font-size:9.5px;color:var(--accent-purple);font-weight:600;margin-bottom:2px;}
.paper-summary{font-size:11px;color:var(--ink-mid);line-height:1.55;}
.gh-stars{font-size:9.5px;color:var(--accent-purple);font-weight:700;margin-bottom:2px;}
a.gh-link{font-size:12px;font-weight:700;color:var(--ink);text-decoration:none;display:block;margin-bottom:2px;}
a.gh-link:hover{color:var(--accent-purple);}
.gh-summary{font-size:11px;color:var(--ink-mid);line-height:1.55;}
a.model-name{font-family:'Noto Sans SC',monospace;font-size:11.5px;font-weight:700;color:var(--accent-orange);text-decoration:none;display:block;line-height:1.4;margin-bottom:2px;word-break:break-all;}
a.model-name:hover{color:var(--accent);}
.model-meta{font-size:9.5px;color:var(--accent-orange);font-weight:600;margin-bottom:2px;}
.model-summary{font-size:11px;color:var(--ink-mid);line-height:1.55;}
.multi-col{columns:2;column-gap:16px;}
.multi-col .story,.multi-col .paper-item,.multi-col .github-item,.multi-col .model-item,.multi-col .hbox{break-inside:avoid;}
.footer{border-top:2px solid var(--ink);margin-top:8px;padding:5px 0;font-size:10px;color:var(--ink-faint);display:flex;justify-content:space-between;letter-spacing:.05em;}
@media(max-width:900px){.main-grid{grid-template-columns:1fr 1fr;}.col-right{border-left:1px solid var(--rule-light);padding-left:10px;}.multi-col{columns:1;}}
@media(max-width:600px){.main-grid{grid-template-columns:1fr;}.col-left,.col-mid{border-right:none;padding-right:0;}.col-right{border-left:none;padding-left:0;}}
"""


def build_html(data, archive_filename):
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    date_str = today.strftime("%Y年%-m月%-d日")
    kp_items = "".join(f'<div class="kp-item"><strong>{esc(k)}</strong></div>' for k in data.get("key_points", []))
    summary_blocks = "".join(
        hbox_html(s["title"], esc(s["content"]), s.get("color", "gold"))
        for s in data.get("summary", [])
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI汽车科技每周情报 | {date_str} 第{issue}期</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700;900&family=Noto+Sans+SC:wght@400;500;700&family=Noto+Sans+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div id="root">
<header class="masthead">
<div class="mh-left">{date_str} · 星期三<br>第 {issue} 期 · 总第 {issue+484} 期<br>归档：{archive_filename}</div>
<div class="mh-center"><h1>AI · 汽车科技每周情报</h1><div class="sub">AI科技 · 车企动态 · 汽车AI · 模型新闻 · 技术论文 · GitHub开源</div></div>
<div class="mh-right">关键词：情报<br>订阅：钉钉群推送</div>
</header>
<div class="kp-bar">{kp_items}</div>
<div class="main-grid">
<div class="col col-left">
<div class="sec-hdr"><span class="sec-num accent">01</span><div class="sec-rule" style="background:var(--accent);"></div><span class="sec-title accent">AI 圈 新 闻</span></div>
<div class="multi-col">{stories_html(data.get("ai_news", []))}</div>
<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num accent">06</span><div class="sec-rule" style="background:var(--accent);"></div><span class="sec-title accent">AI 圈 深 度</span></div>
<div class="multi-col">{stories_html(data.get("ai_deep", []))}</div>
<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num gold">09</span><div class="sec-rule" style="background:var(--accent-gold);"></div><span class="sec-title gold">本 周 总 结</span></div>
<div class="multi-col">{summary_blocks}</div>
</div>
<div class="col col-mid">
<div class="sec-hdr"><span class="sec-num blue">02</span><div class="sec-rule" style="background:var(--accent-blue);"></div><span class="sec-title blue">车 企 科 技</span></div>
<div class="multi-col">{stories_html(data.get("auto_tech", []))}</div>
<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num gold">03</span><div class="sec-rule" style="background:var(--accent-gold);"></div><span class="sec-title gold">领 导 变 动</span></div>
<div class="multi-col">{leadership_html(data.get("leadership", []))}</div>
<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num green">04</span><div class="sec-rule" style="background:var(--accent-green);"></div><span class="sec-title green">汽 车 AI 技 术</span></div>
<div class="multi-col">{stories_html(data.get("auto_ai", []))}</div>
</div>
<div class="col col-right">
<div class="sec-hdr"><span class="sec-num purple">05</span><div class="sec-rule" style="background:var(--accent-purple);"></div><span class="sec-title purple">技 术 论 文</span></div>
<div class="multi-col">{paper_html(data.get("papers", []))}</div>
<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num orange">07</span><div class="sec-rule" style="background:var(--accent-orange);"></div><span class="sec-title orange">HuggingFace 模 型</span></div>
<div class="multi-col">{models_html(data.get("models", []))}</div>
<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num purple">08</span><div class="sec-rule" style="background:var(--accent-purple);"></div><span class="sec-title purple">GitHub 开 源</span></div>
<div class="multi-col">{gh_html(data.get("github", []))}</div>
</div>
</div>
<footer class="footer"><span>📡 本情报由 Mavis 每周自动抓取整理</span><span>数据源：arXiv + GitHub + HF + 7 大 RSS</span><span>第 {issue} 期 · {date_str}</span></footer>
</div>
</body>
</html>"""


# ========== 5. 主流程 ==========
def main():
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    week_tag = today.strftime("%Y%m%d")
    archive_filename = f"{week_tag}-issue{issue}.html"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    archive_path = os.path.join(OUTPUT_DIR, archive_filename)

    # Step 1: 抓取
    raw = fetch_all()
    print(f"\n📦 总计: AI 论文 {len(raw['papers_ai']) + len(raw['papers_ro']) + len(raw['papers_cl'])} 篇 | AI 巨头 {len(raw['ai_giants'])} | 车企 {len(raw['auto_companies'])} | 中文 {len(raw['cn_tech'])} | HN {len(raw['hn'])} | HF 模型 {len(raw['hf_models'])}")

    raw_path = os.path.join(OUTPUT_DIR, f"raw-{week_tag}.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    # Step 2: AI 整理
    news_data = call_llm(raw)
    print(f"📰 AI 整理完成，模块数: {len(news_data)}")

    json_path = os.path.join(OUTPUT_DIR, f"data-{week_tag}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)

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
