#!/usr/bin/env python3
"""
fetch_news_sources.py — 抓取车企 / AI 巨头官网新闻 + HuggingFace 模型
所有数据源全部免费、无需登录
"""
import re
import json
import requests
from datetime import datetime, timedelta
from html import unescape

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

# ============================================================
# 数据源配置
# ============================================================
AI_GIANT_RSS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Anthropic": "https://www.anthropic.com/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "DeepMind": "https://deepmind.google/blog/rss.xml",
    "NVIDIA": "https://blogs.nvidia.com/feed/",
    "HuggingFace": "https://huggingface.co/blog/feed.xml",
    "PyTorch": "https://pytorch.org/feed.xml",
}

AUTO_COMPANY_RSS = {
    "BMW": "https://www.press.bmwgroup.com/global/rss",
    "Volkswagen": "https://www.volkswagen-newsroom.com/de/rss",
    "Hyundai": "https://www.hyundaimotorgroup.com/en/news/rss.do",
    "Polestar": "https://media.polestar.com/rss",
    "Volvo": "https://www.media.volvocars.com/global/rss",
    "Ford": "https://media.ford.com/content/fordmedia/feeds/us/news.rss",
    "GM": "https://media.gm.com/media/us/en/gm/news.rss",
    "BYD": "https://www.bydeurope.com/rss",
    "XPeng": "https://www.xiaopeng.com/news/rss",
    "Li Auto": "https://www.lixiang.com/news/rss",
}

CN_TECH_RSS = {
    "爱范儿": "https://www.ifanr.com/feed",
    "极客公园": "https://www.geekpark.net/rss",
    "IT之家": "https://www.ithome.com/rss/",
    "36氪": "https://36kr.com/feed",
    "钛媒体": "https://www.tmtpost.com/rss.xml",
    "新浪科技": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num=20&versionNumber=1.2.4&page=1",
}

HN_API = "https://hn.algolia.com/api/v1/search?tags=story&numericFilters=points>=50,created_at_i>{}"


# ============================================================
# RSS 抓取（统一处理）
# ============================================================
def fetch_rss(url, source_name, max_items=5, days_limit=7):
    """抓取 RSS，最近 N 天内的前 max_items 条"""
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
        # 发布时间
        pub = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            pub = datetime(*entry.updated_parsed[:6])
        if pub and pub < cutoff:
            continue
        title = re.sub(r"\s+", " ", entry.get("title", "")).strip()
        summary = re.sub(r"\s+", " ", unescape(entry.get("summary", entry.get("description", "")))).strip()
        # 去掉 HTML 标签
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
def fetch_hn(max_items=10):
    """Hacker News 当周高赞"""
    seven_days_ago = int((datetime.now() - timedelta(days=7)).timestamp())
    url = HN_API.format(seven_days_ago)
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
    except Exception as e:
        print(f"  [WARN] HN: {e}")
        return []
    # 关键词过滤：AI / ML / agent / 模型 / robot
    keywords = ["ai", "ml", "llm", "gpt", "claude", "agent", "model", "robot", "deep learning", "transformer", "openai", "anthropic", "hugging"]
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
def fetch_hf_models(limit=15, days_limit=30):
    """HF 热门模型：先按 likes 排序（社交热度），再按 downloads 补"""
    cutoff = (datetime.now() - timedelta(days=days_limit)).strftime("%Y-%m-%d")
    # 改用 likes 排序，更能反映社区认可
    url = f"https://huggingface.co/api/models?sort=likes&direction=-1&limit=50&full=false"
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "ai-weekly-bot/1.0"})
        resp.raise_for_status()
        models = resp.json()
    except Exception as e:
        print(f"  [WARN] HF models: {e}")
        return []

    # 二次过滤：最近 30 天有更新 + likes >= 10
    recent = []
    for m in models:
        last_mod = m.get("lastModified", "")
        likes = m.get("likes", 0)
        # 排除太老或太小
        if last_mod >= cutoff and likes >= 10:
            recent.append(m)
        if len(recent) >= limit * 2:
            break

    # 如果按时间过滤后不够，用 likes top-N 补
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
        # 简化大数字
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

    # 按 likes 降序
    items.sort(key=lambda x: x["likes"], reverse=True)
    print(f"  [OK] HuggingFace 模型: {len(items)} 个")
    return items[:limit]


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60)
    print("📡 抓取车企 / AI 巨头 + HF 模型 + HN")
    print("=" * 60)

    data = {"fetched_at": datetime.now().isoformat()}

    # 1. AI 巨头
    print("\n🤖 AI 巨头官网 RSS...")
    ai_giants = []
    for name, url in AI_GIANT_RSS.items():
        ai_giants.extend(fetch_rss(url, name, max_items=3))
    data["ai_giants"] = ai_giants

    # 2. 车企
    print("\n🚗 车企官网 RSS...")
    auto_companies = []
    for name, url in AUTO_COMPANY_RSS.items():
        auto_companies.extend(fetch_rss(url, name, max_items=3))
    data["auto_companies"] = auto_companies

    # 3. 中文科技媒体
    print("\n📰 中文科技媒体 RSS...")
    cn_tech = []
    for name, url in CN_TECH_RSS.items():
        cn_tech.extend(fetch_rss(url, name, max_items=3))
    data["cn_tech"] = cn_tech

    # 4. Hacker News
    print("\n💬 Hacker News...")
    data["hn"] = fetch_hn(max_items=10)

    # 5. HuggingFace 模型
    print("\n🤗 HuggingFace 模型...")
    data["hf_models"] = fetch_hf_models(limit=15)

    # 保存
    out = f"news_sources_{datetime.now().strftime('%Y%m%d')}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 保存到: {out}")
    print(f"📊 统计: AI 巨头 {len(ai_giants)} | 车企 {len(auto_companies)} | 中文 {len(cn_tech)} | HN {len(data['hn'])} | HF 模型 {len(data['hf_models'])}")

    # 预览
    print("\n" + "=" * 60)
    print("📋 AI 巨头新闻预览:")
    print("=" * 60)
    for item in ai_giants[:3]:
        print(f"\n• [{item['source']}] {item['title'][:80]}")

    print("\n" + "=" * 60)
    print("📋 车企新闻预览:")
    print("=" * 60)
    for item in auto_companies[:3]:
        print(f"\n• [{item['source']}] {item['title'][:80]}")

    print("\n" + "=" * 60)
    print("🤗 HuggingFace 模型预览（按 likes 排序）:")
    print("=" * 60)
    for m in data["hf_models"][:5]:
        print(f"\n⭐ {m['title']}")
        print(f"  {m['summary']}")
        print(f"  🔗 {m['link']}")

    return data


if __name__ == "__main__":
    main()
