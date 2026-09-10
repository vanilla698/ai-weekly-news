#!/usr/bin/env python3
"""
fetch_news_sources.py — 根据 sources.json 抓取各模块数据
所有数据源全部免费、无需登录
"""
import re
import json
import os
import requests
from datetime import datetime, timedelta
from html import unescape

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

# 加载配置文件
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "sources.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"[WARN] {CONFIG_PATH} not found, using defaults")
        return None
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# RSS 抓取
# ============================================================
def fetch_rss(url, source_name, max_items=5, days_limit=7):
    if not HAS_FEEDPARSER:
        print(f"  [SKIP] {source_name}: feedparser not installed")
        return []
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "ai-weekly-bot/1.0"})
        resp.raise_for_status()
    except Exception as e:
        print(f"  [WARN] {source_name}: {e}")
        return []
    feed = feedparser.parse(resp.content)
    if not feed.entries:
        print(f"  [WARN] {source_name}: 0 entries")
        return []
    cutoff = datetime.now() - timedelta(days=days_limit)
    items = []
    for entry in feed.entries[:max_items * 2]:
        pub = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            pub = datetime(*entry.updated_parsed[:6])
        if pub and pub < cutoff:
            continue
        title = re.sub(r"\s+", " ", entry.get("title", "")).strip()
        summary = re.sub(r"\s+", " ", unescape(entry.get("summary", entry.get("description", "")))).strip()
        summary = re.sub(r"<[^>]+>", "", summary)[:200]
        link = entry.get("link", "")
        if title and link:
            items.append({
                "title": title,
                "summary": summary,
                "link": link,
                "source": source_name,
                "published": pub.isoformat() if pub else "",
            })
        if len(items) >= max_items:
            break
    print(f"  [OK] {source_name}: {len(items)} 条")
    return items


# ============================================================
# Hacker News
# ============================================================
def fetch_hn(max_items=6, min_points=50, days=7, keywords=None):
    if keywords is None:
        keywords = ["ai", "ml", "llm", "gpt", "claude", "agent", "model", "robot"]
    cutoff = int((datetime.now() - timedelta(days=days)).timestamp())
    url = f"https://hn.algolia.com/api/v1/search?tags=story&numericFilters=points>={min_points},created_at_i>{cutoff}"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
    except Exception as e:
        print(f"  [WARN] HN: {e}")
        return []
    filtered = [h for h in hits if any(k in (h.get("title") or "").lower() for k in keywords)]
    items = []
    for h in (filtered or hits)[:max_items]:
        items.append({
            "title": h.get("title", ""),
            "summary": f"💬 {h.get('num_comments', 0)} 评论 · ⬆️ {h.get('points', 0)} 赞",
            "link": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID', '')}",
            "source": "Hacker News",
        })
    print(f"  [OK] Hacker News: {len(items)} 条")
    return items


# ============================================================
# HuggingFace 模型
# ============================================================
def fetch_hf_models(limit=15, days_limit=30, min_likes=10):
    cutoff = (datetime.now() - timedelta(days=days_limit)).strftime("%Y-%m-%d")
    url = f"https://huggingface.co/api/models?sort=likes&direction=-1&limit=50&full=false"
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "ai-weekly-bot/1.0"})
        resp.raise_for_status()
        models = resp.json()
    except Exception as e:
        print(f"  [WARN] HF models: {e}")
        return []

    recent = []
    for m in models:
        last_mod = m.get("lastModified", "")
        likes = m.get("likes", 0)
        if last_mod >= cutoff and likes >= min_likes:
            recent.append(m)
        if len(recent) >= limit * 2:
            break

    if len(recent) < limit:
        for m in models:
            if m.get("likes", 0) >= 50 and m not in recent:
                recent.append(m)
            if len(recent) >= limit:
                break

    items = []
    for m in recent[:limit]:
        model_id = m.get("id", m.get("modelId", ""))
        if not model_id:
            continue
        pipeline = m.get("pipeline_tag", "通用模型")
        downloads = m.get("downloads", 0)
        likes = m.get("likes", 0)
        if downloads >= 1000:
            dl_str = f"{downloads/1000:.1f}k" if downloads < 1000000 else f"{downloads/1000000:.1f}M"
        else:
            dl_str = str(downloads)
        items.append({
            "model_id": model_id,
            "title": model_id,
            "pipeline": pipeline,
            "downloads": downloads,
            "likes": likes,
            "downloads_str": dl_str,
            "summary": f"📥 {dl_str} 下载 · ⭐ {likes} 赞 · 🏷️ {pipeline}",
            "link": f"https://huggingface.co/{model_id}",
        })

    items.sort(key=lambda x: x["likes"], reverse=True)
    print(f"  [OK] HuggingFace 模型: {len(items)} 个")
    return items[:limit]


# ============================================================
# arXiv
# ============================================================
def fetch_arxiv(category="cs.AI", max_results=8):
    url = f"http://export.arxiv.org/api/query?search_query=cat:{category}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [WARN] arxiv {category}: {e}")
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


# ============================================================
# 工具：保证偶数条目
# ============================================================
def ensure_even(items, source_pool=None, source_name=""):
    """保证返回列表的条目数是偶数；奇数时从 source_pool 补一条"""
    if not items:
        return items
    if len(items) % 2 == 0:
        return items
    if source_pool and len(source_pool) > len(items):
        # 从 source_pool 找一个不同标题的
        existing_titles = {it.get("title", "")[:50] for it in items}
        for extra in source_pool:
            if extra.get("title", "")[:50] not in existing_titles:
                items.append(extra)
                print(f"  [+1] 从 {source_name} 补一条: {extra.get('title', '')[:50]}")
                break
    # 如果还是奇数，去掉最后一条
    if len(items) % 2 == 1:
        items = items[:-1]
    return items


# ============================================================
# 主流程（从 sources.json 加载）
# ============================================================
def main():
    config = load_config()
    if not config:
        return None

    modules = config.get("modules", {})
    data = {"fetched_at": datetime.now().isoformat()}

    # 1. AI 巨头
    ai_cfg = modules.get("ai_giants", {})
    if ai_cfg.get("enabled", True):
        print("\n🤖 抓取 AI 巨头官网...")
        items = []
        for src in ai_cfg.get("sources", []):
            items.extend(fetch_rss(src["url"], src["name"], max_items=ai_cfg.get("max_items", 3)))
        data["ai_giants"] = ensure_even(items, items, "ai_giants")

    # 2. 车企
    auto_cfg = modules.get("auto_companies", {})
    if auto_cfg.get("enabled", True):
        print("\n🚗 抓取车企官网...")
        items = []
        for src in auto_cfg.get("sources", []):
            items.extend(fetch_rss(src["url"], src["name"], max_items=auto_cfg.get("max_items", 3)))
        data["auto_companies"] = ensure_even(items, items, "auto_companies")

    # 3. 中文科技媒体
    cn_cfg = modules.get("cn_tech", {})
    if cn_cfg.get("enabled", True):
        print("\n📰 抓取中文科技媒体...")
        items = []
        for src in cn_cfg.get("sources", []):
            items.extend(fetch_rss(src["url"], src["name"], max_items=cn_cfg.get("max_items", 3)))
        data["cn_tech"] = ensure_even(items, items, "cn_tech")

    # 4. arXiv
    arxiv_cfg = modules.get("arxiv", {})
    if arxiv_cfg.get("enabled", True):
        print("\n🔬 抓取 arXiv 论文...")
        papers_ai = fetch_arxiv("cs.AI", arxiv_cfg.get("max_per_category", 8))
        papers_ro = fetch_arxiv("cs.RO", arxiv_cfg.get("max_per_category", 8))
        papers_cl = fetch_arxiv("cs.CL", arxiv_cfg.get("max_per_category", 8))
        print(f"  cs.AI {len(papers_ai)} | cs.RO {len(papers_ro)} | cs.CL {len(papers_cl)}")
        data["papers_ai"] = ensure_even(papers_ai, papers_ai + papers_ro + papers_cl, "arxiv")
        data["papers_ro"] = ensure_even(papers_ro, papers_ai + papers_cl, "arxiv")
        data["papers_cl"] = ensure_even(papers_cl, papers_ai + papers_ro, "arxiv")

    # 5. Hacker News
    hn_cfg = modules.get("hacker_news", {})
    if hn_cfg.get("enabled", True):
        print("\n💬 抓取 Hacker News...")
        data["hn"] = fetch_hn(
            max_items=hn_cfg.get("max_items", 6),
            min_points=hn_cfg.get("min_points", 50),
            days=hn_cfg.get("days", 7),
            keywords=hn_cfg.get("keywords"),
        )

    # 6. HuggingFace 模型
    hf_cfg = modules.get("huggingface_models", {})
    if hf_cfg.get("enabled", True):
        print("\n🤗 抓取 HuggingFace 模型...")
        data["hf_models"] = fetch_hf_models(
            limit=hf_cfg.get("max_items", 15),
            days_limit=hf_cfg.get("days_limit", 30),
            min_likes=hf_cfg.get("min_likes", 10),
        )

    out = f"news_sources_{datetime.now().strftime('%Y%m%d-%H%M')}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 保存到: {out}")
    return data


if __name__ == "__main__":
    main()
