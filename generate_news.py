# AI 汽车科技每周情报 · 生成脚本
import json
import os
from datetime import datetime

OUTPUT_HTML = "ai_auto_news_preview.html"
OUTPUT_JSON = "news_data.json"

NEWS_DATA = {
    "key_points": [
        "🤖 Claude Fable 5.1：成本↓25%，Agent任务成本最高↓45%，多项基准超越GPT-5.6 Sol",
        "💰 英伟达收购HF：129亿美元，若完成成AI领域最大收购",
        "🔔 车企人事密集调整：李书福辞任吉利董事会主席，Stellantis同日完成三大品牌CEO换帅",
        "🤝 具身智能爆发：小鹏机器人估值63亿美元；DeepSeek V4 Flash Vision开源",
    ],
    "ai_news": [
        {"title": "Anthropic 发布 Claude Fable 5.1，典型任务成本降低 25%", "summary": "Agent 化任务成本最高降 45%，缓存读取价格降低 75%，长周期任务能力大幅强化，多项基准超越 GPT-5.6 Sol。", "link": "https://news.qq.com/rain/a/20260902A03TQ800", "source": "腾讯新闻"},
        {"title": "英伟达 129 亿美元收购 Hugging Face，AI 最大收购案", "summary": "英伟达从 GPU 延伸至开源模型生态核心入口，收购若完成将改写 AI 产业格局。", "link": "https://www.163.com/dy/article/L5O0SEHT0556L4CJ.html", "source": "网易"},
        {"title": "DeepSeek V4 Flash Vision 开源多模态模型正式发布", "summary": "MIT 许可开源，添加视觉理解能力，保持与 V4 Flash 相当的文本 Agent 性能。", "link": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp", "source": "Hugging Face"},
        {"title": "OpenAI 广告业务年化营收突破 10 亿美元，上线仅 200 天", "summary": "嵌入 ChatGPT 对话场景与 DALL-E 内容页，预计 2026 年全年广告收入达 12.7 亿美元。", "link": "https://www.zhiguf.com/focusnews_detail/2335689", "source": "指股网"},
    ],
    "auto_tech": [
        {"title": "小鹏机器人首轮融资超 9 亿美元，估值突破 63 亿美元", "summary": "刷新中国具身智能单轮私募融资纪录，投资方包括 IDG、腾讯、阿里等。", "link": "https://www.163.com/dy/article/L5O0SEHT0556L4CJ.html", "source": "网易"},
        {"title": "比亚迪天神之眼成本降至 5000 元以内，10 万级国民车也能城市 NOA", "summary": "成功搭载于起售价仅 7.88 万元的海鸥车型，智驾功能进一步下探大众市场。", "link": "https://hj.pcauto.com.cn/article/3198054", "source": "太平洋汽车"},
        {"title": "努比亚 NaviX Ultra 入网，全球首款 AI 智能体手机 9 月上市", "summary": "搭载豆包手机助手，可跨应用执行订票、导航等多步骤任务。", "link": "https://new.qq.com/rain/a/20260902A03BKD00", "source": "腾讯网"},
        {"title": "英伟达 FY27 Q2 财报超预期，2028 财年增长指引约 70%", "summary": "AI 服务器订单和积压订单同步大增，光通信、超节点国产算力、液冷三条主线迎催化窗口。", "link": "https://new.qq.com/rain/a/20260902A03HAX00", "source": "腾讯网"},
        {"title": "戴尔多业务线联动，AI 服务器积压订单 950 亿美元创新高", "summary": "营收同比增长 58% 至 470 亿美元创历史新高，全年指引上调 250 亿美元。", "link": "https://news.qq.com/rain/a/20260902A03TQ800", "source": "腾讯新闻"},
    ],
    "leadership": [
        {"title": "李书福辞任吉利汽车董事会主席，安聪慧接任", "summary": "获任终身荣誉主席，淦家阅任行政总裁。李：\"汽车产业是没有尽头的马拉松。\"", "link": "https://www.zgswcn.com/news.html?aid=366950", "source": "中国商报网"},
        {"title": "东风汽车副总经理黄勇调任中国航空工业集团", "summary": "曾任一汽丰田党委书记，调任中航工业集团董事、党组副书记。", "link": "https://www.toutiao.com/article/7680572878546420234", "source": "头条"},
        {"title": "Stellantis：Arnaud Belloni 重返，任菲亚特/阿巴斯/蓝旗亚 CEO", "summary": "9月1日生效，兼任欧洲区首席营销官。Xavier Chardon 兼任 DS 品牌 CEO。", "link": "https://www.just-auto.com/news/arnaud-belloni-fiat-abarth-lancia-ceo", "source": "Stellantis 官方"},
        {"title": "Kevin Barbian 接任奔驰马来西亚 COO", "summary": "9月1日正式出任，曾主导 Mercedes-EQ 数字化转型及\"零售未来\"计划。", "link": "https://www.carsifu.my/news/kevin-barbian-is-new-coo-of-mercedes-benz-cars-malaysia", "source": "CarSifu"},
    ],
    "auto_ai": [
        {"title": "天工 Ultra 夺冠全球首个人形机器人半程马拉松", "summary": "北京人形机器人创新中心研发，在结构设计、动力驱动、多模态传感器融合方面取得重大突破。", "link": "https://www.gov.cn", "source": "政府公告"},
        {"title": "高盛：人形机器人整机均价 2035 年降至 2.13 万美元", "summary": "整机均价将从 2025 年的 4.18 万美元降至 2035 年的 2.13 万美元，降幅约 49%。", "link": "https://ai.yesky.com/439/369939.shtml", "source": "天极网"},
        {"title": "华为 + 阿里 9 月双大会密集召开，国产算力再迎催化", "summary": "9月17-19日华为全联接大会、22-24日阿里云栖大会将密集发布超节点与算力基础设施进展。", "link": "https://new.qq.com/rain/a/20260902A03HAX00", "source": "腾讯网"},
        {"title": "DeepSeek 赋能智能座舱，20 余家车企宣布融合", "summary": "比亚迪、吉利、奇瑞、长安、东风等 20 余家车企与 DeepSeek 达成技术融合。", "link": "https://world.huanqiu.com", "source": "环球网"},
        {"title": "工信部：年内培育超 2000 家 AI 应用服务商", "summary": "2026 年底 AI 应用服务商资源池突破 2000 家，2025 年 AI 核心产业规模已超 1.2 万亿元。", "link": "https://www.zhiguf.com/focusnews_detail/2335689", "source": "指股网"},
    ],
    "papers": [
        {"title": "DS-Lighting — 数据科学自动化 Agent 工具包", "id": "2608.28590", "authors": "港科大", "summary": "统一 Agent 工具包，将任务表示、执行状态、输出约束和评估反馈显式化，提升数据科学工作流可复现性。"},
        {"title": "Aspire — 模型能否从模糊目标自主进化？", "id": "2608.31111", "authors": "ByteDance", "summary": "首个模糊目标驱动的自进化基准，Agent 须自主诊断能力缺口、构建训练信号。权重级增益仍不稳定。"},
        {"title": "NavMCP — 将基础模型搭建为物理世界智能体", "id": "2608.30396", "authors": "上交大 + 阿里", "summary": "结合 VLM 推理智能体与 NFM 执行器实现长时程导航，在 Unitree Go2 机器人上验证优于基线。"},
        {"title": "Answer Probing — LLM 多样化解决方案探索", "id": "2608.30345", "authors": "中科大 + 清华", "summary": "APTS 树搜索方法提升多推理任务的解决方案多样性，经实验证实有效性与鲁棒性。"},
        {"title": "Thea — 具身智能体的 Harness 范式", "id": "2608.11246", "authors": "arXiv cs.AI/cs.RO", "summary": "将编码 Agent 的 Harness 范式扩展至物理世界，引入 Scene Graph as Context，在真实环境中完成长时程任务。"},
        {"title": "Rapid On-Robot Learning — 机器人快速学习动态操控技能", "id": "2608.26800", "authors": "arXiv cs.RO", "summary": "双手机器人在 5 分钟真实交互中学会 5 种杂耍模式，regularized memory-based learning 在 sim2real 差距下仍有效。"},
        {"title": "Gating Before Commitment — 自动驾驶意图分歧检测", "id": "2608.26074", "authors": "arXiv cs.RO", "summary": "在车辆执行操作前检测意图分歧，防止交互后决策失败，为自动驾驶安全提供新框架。"},
    ],
    "github": [
        {"name": "deepseek-ai/deepseek-harness", "stars": "206k", "summary": "DeepSeek 官方 Agent 开发框架，\"万物皆插件\"，Standard/PTC/Minimal/Creative 四种运行模式。MIT 许可。", "link": "https://github.com/deepseek-ai/deepseek-harness"},
        {"name": "calesthio/OpenMontage", "stars": "32k", "summary": "开源 AI 视频制作系统，12 条生产流水线，$0.15~$1.33 生成完整视频。", "link": "https://github.com/calesthio/OpenMontage"},
        {"name": "topoteretes/cognee", "stars": "29.6k", "summary": "向量嵌入 + 知识图谱为 Agent 提供跨会话持久化长时记忆，兼容 Claude Code、Codex、Cursor。", "link": "https://github.com/topoteretes/cognee"},
        {"name": "openai/codex", "stars": "116k", "summary": "OpenAI 开源轻量级终端编码 Agent，Rust 编写，支持 VS Code、Cursor、Windsurf。ChatGPT Plus/Pro 内置。", "link": "https://github.com/openai/codex"},
        {"name": "usail-hkust/dslighting", "stars": "33", "summary": "港科大 DS-Lighting 完整源码仓库，含数据/工作流/执行/评估四层架构，AGPL-3.0 许可。", "link": "https://github.com/usail-hkust/dslighting"},
    ],
    "ai_deep": [
        {"title": "马斯克：AI 或令全球经济年增 20~30 万亿美元", "summary": "G20 连线预测人形机器人十年内将达 10 亿台；2027 年底 AI 或可完成几乎所有数字化工作。", "link": "https://news.qq.com/rain/a/20260902A03TQ800", "source": "腾讯新闻"},
        {"title": "OpenAI 断供 Cursor，Anthropic 随即表态支持 Claude", "summary": "OpenAI 因 SpaceX 违约终止向 Cursor 供模，Anthropic 迅速增加算力支持 Claude 部署。", "link": "https://new.qq.com/rain/a/20260902A03BKD00", "source": "腾讯网"},
        {"title": "宇树科技股价接近\"腰斩\"，人形机器人资本降温", "summary": "股价相比上市首日跌幅达 48.6%，人形机器人板块资本热度出现分化。", "link": "https://ai.yesky.com/439/369939.shtml", "source": "天极网"},
    ],
    "summary": [
        {"title": "大模型竞争全面转向性价比", "content": "Claude Fable 5.1 成本大降 25%~45%，DeepSeek V4 Flash Vision 开源多模态——性能差距收窄，性价比成核心竞争力。", "color": "gold"},
        {"title": "车企人事密集调整，跨国联动成主旋律", "content": "李书福辞任吉利董事会主席，Stellantis 同期完成欧洲区高管大换血，东风黄勇调任中航工业。", "color": "gold"},
        {"title": "具身智能融资爆发，资本开始分化", "content": "小鹏机器人估值 63 亿，天工 Ultra 夺冠马拉松；但宇树股价腰斩，纯概念炒作退潮。", "color": "gold"},
        {"title": "汽车 AI 从\"尝鲜\"走向\"刚需\"", "content": "比亚迪智驾下探至 7.88 万、NaviX Ultra 入网、DeepSeek 赋能座舱——汽车 AI 化从高端标配走向大众刚需。", "color": "green"},
        {"title": "AI 技术论文与开源生态并进", "content": "DeepSeek V4 Flash Vision 开源多模态、微软 FaultSense 提升 MoE 推理可靠性；DeepSeek Harness 206k star，Agent 基础设施走向成熟。", "color": "purple"},
    ],
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def stories_html(items):
    return "".join(
        '<div class="story">'
        f'<a class="link-title" href="{esc(item["link"])}" target="_blank">{esc(item["title"])}</a>'
        f'<div class="story-summary">{esc(item["summary"])}</div>'
        f'<div class="story-meta"><a href="{esc(item["link"])}" target="_blank">{esc(item["source"])} →</a></div>'
        '</div>'
        for item in items
    )


def hbox_html(title, content, color):
    return (
        f'<div class="hbox {color}">'
        f'<strong>{esc(title)}</strong>{content}'
        '</div>'
    )


def paper_html(papers):
    return "".join(
        '<div class="paper-item">'
        f'<a class="paper-link" href="https://arxiv.org/abs/{p["id"]}" target="_blank">{esc(p["title"])}</a>'
        f'<div class="paper-meta">{esc(p["authors"])} · arXiv:{p["id"]}</div>'
        f'<div class="paper-summary">{esc(p["summary"])}</div>'
        '</div>'
        for p in papers
    )


def gh_html(ghs):
    return "".join(
        '<div class="github-item">'
        f'<div class="gh-stars">&#9733; {esc(g["name"])} — {g["stars"]} stars</div>'
        f'<a class="gh-link" href="{g["link"]}" target="_blank">{esc(g["name"])}</a>'
        f'<div class="gh-summary">{esc(g["summary"])}</div>'
        '</div>'
        for g in ghs
    )


def build_html(data):
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    date_str = today.strftime("%Y年%-m月%-d日")

    kp_items = "".join(
        f'<div class="kp-item"><strong>{esc(k)}</strong></div>'
        for k in data["key_points"]
    )

    summary_blocks = "".join(
        hbox_html(s["title"], esc(s["content"]), s["color"])
        for s in data["summary"]
    )

    leadership_blocks = "".join(
        hbox_html(
            item["title"],
            f'{esc(item["summary"])}<div class="src"><a href="{esc(item["link"])}" target="_blank">来源：{esc(item["source"])} &#8594;</a></div>',
            "gold",
        )
        for item in data["leadership"]
    )

    return "\n".join([
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>AI汽车科技每周情报 | {date_str}</title>",
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700;900&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">',
        "<style>",
        ":root{--ink:#111;--ink-mid:#3a3a3a;--ink-light:#666;--ink-faint:#999;--rule:#222;--rule-light:#ddd;--accent:#c0392b;--accent-blue:#1a3a5c;--accent-gold:#8b6914;--accent-green:#1a5c2a;--accent-purple:#5c1a5c;--paper:#faf9f6;--paper-dark:#ede9e0;}",
        "* {margin:0;padding:0;box-sizing:border-box}",
        "body{font-family:'Noto Sans SC',sans-serif;background:var(--paper);color:var(--ink);font-size:13px;line-height:1.5;}",
        "#root{width:90vw;margin:0 auto;}",
        ".masthead{border-top:4px solid var(--ink);border-bottom:2px solid var(--ink);padding:6px 0 5px;margin-bottom:8px;display:flex;align-items:center;}",
        ".mh-left{font-size:10px;color:var(--ink-light);line-height:1.8;white-space:nowrap;}",
        ".mh-center{flex:1;text-align:center;}",
        ".mh-center h1{font-family:'Noto Serif SC',serif;font-size:clamp(20px,3.5vw,38px);font-weight:900;letter-spacing:.18em;line-height:1.1;}",
        ".mh-center .sub{font-size:clamp(9px,1vw,11px);letter-spacing:.25em;color:var(--ink-light);margin-top:2px;}",
        ".mh-right{font-size:10px;color:var(--ink-light);line-height:1.8;text-align:right;white-space:nowrap;}",
        ".kp-bar{display:flex;gap:0;border:1.5px solid var(--ink);margin-bottom:6px;flex-wrap:wrap;}",
        ".kp-item{flex:1;min-width:180px;padding:7px 10px;border-right:1.5px solid var(--ink);font-size:11.5px;line-height:1.5;color:var(--ink-mid);}",
        ".kp-item:last-child{border-right:none;}",
        ".kp-item strong{color:var(--ink);font-size:12px;display:block;}",
        ".sec-hdr{display:flex;align-items:center;gap:8px;margin:8px 0 5px;}",
        ".sec-num{font-family:'Noto Serif SC',serif;font-size:11px;font-weight:700;color:#fff;background:var(--ink);padding:1px 5px;white-space:nowrap;}",
        ".sec-num.blue{background:var(--accent-blue);}.sec-num.gold{background:var(--accent-gold);}.sec-num.green{background:var(--accent-green);}.sec-num.purple{background:var(--accent-purple);}.sec-num.accent{background:var(--accent);}",
        ".sec-rule{flex:1;height:1.5px;}",
        ".sec-title{font-family:'Noto Serif SC',serif;font-size:clamp(13px,1.8vw,16px);font-weight:700;white-space:nowrap;letter-spacing:.08em;}",
        ".sec-title.accent{color:var(--accent);}.sec-title.blue{color:var(--accent-blue);}.sec-title.gold{color:var(--accent-gold);}.sec-title.green{color:var(--accent-green);}.sec-title.purple{color:var(--accent-purple);}",
        ".main-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0;align-items:start;}",
        ".col{display:flex;flex-direction:column;gap:0;}",
        ".col-left{border-right:1px solid var(--rule-light);padding-right:10px;}",
        ".col-mid{border-right:1px solid var(--rule-light);padding:0 10px;}",
        ".col-right{padding-left:10px;}",
        ".story{padding:5px 0;border-bottom:1px dashed var(--rule-light);}",
        ".story:last-child{border-bottom:none;}",
        "a.link-title{font-family:'Noto Serif SC',serif;font-size:13px;font-weight:700;color:var(--ink);text-decoration:none;display:block;line-height:1.4;}",
        "a.link-title:hover{color:var(--accent);}",
        ".story-summary{font-size:11.5px;color:var(--ink-mid);line-height:1.55;margin-top:3px;}",
        ".story-meta{font-size:10px;color:var(--accent);margin-top:3px;font-weight:500;}",
        ".story-meta a{color:var(--accent);text-decoration:none;}",
        ".story-meta a:hover{text-decoration:underline;}",
        ".hbox{border-top:2.5px solid var(--accent);background:var(--paper-dark);padding:6px 9px;margin:5px 0;font-size:11.5px;line-height:1.6;color:var(--ink-mid);}",
        ".hbox.blue{border-color:var(--accent-blue);}.hbox.gold{border-color:var(--accent-gold);}.hbox.green{border-color:var(--accent-green);}.hbox.purple{border-color:var(--accent-purple);}",
        ".hbox strong{color:var(--ink);font-size:12.5px;display:block;margin-bottom:2px;font-family:'Noto Serif SC',serif;}",
        ".hbox .src{font-size:10px;color:var(--ink-faint);margin-top:3px;}.hbox .src a{color:var(--accent-gold);text-decoration:none;}.hbox .src a:hover{text-decoration:underline;}",
        ".paper-item,.github-item{padding:5px 0;border-bottom:1px dashed var(--rule-light);}",
        ".paper-item:last-child,.github-item:last-child{border-bottom:none;}",
        "a.paper-link{font-family:'Noto Serif SC',serif;font-size:12.5px;font-weight:700;color:var(--ink);text-decoration:none;display:block;line-height:1.4;margin-bottom:2px;}",
        "a.paper-link:hover{color:var(--accent-purple);}",
        ".paper-meta{font-size:9.5px;color:var(--accent-purple);font-weight:600;margin-bottom:2px;}",
        ".paper-summary{font-size:11px;color:var(--ink-mid);line-height:1.55;}",
        ".gh-stars{font-size:9.5px;color:var(--accent-purple);font-weight:700;margin-bottom:2px;}",
        "a.gh-link{font-size:12px;font-weight:700;color:var(--ink);text-decoration:none;display:block;margin-bottom:2px;}",
        "a.gh-link:hover{color:var(--accent-purple);}",
        ".gh-summary{font-size:11px;color:var(--ink-mid);line-height:1.55;}",
        ".multi-col{columns:2;column-gap:16px;}",
        ".multi-col .story,.multi-col .paper-item,.multi-col .github-item,.multi-col .hbox{break-inside:avoid;}",
        ".footer{border-top:2px solid var(--ink);margin-top:8px;padding:5px 0;font-size:10px;color:var(--ink-faint);display:flex;justify-content:space-between;letter-spacing:.05em;}",
        "@media(max-width:900px){.main-grid{grid-template-columns:1fr 1fr;}.col-right{border-left:1px solid var(--rule-light);padding-left:10px;}.multi-col{columns:1;}}",
        "@media(max-width:600px){.main-grid{grid-template-columns:1fr;}.col-left,.col-mid{border-right:none;padding-right:0;}.col-right{border-left:none;padding-left:0;}}",
        "</style>",
        "</head>",
        "<body>",
        '<div id="root">',
        "<header class=\"masthead\">",
        f'<div class="mh-left">{date_str} · 星期三<br>第 {issue} 期 · 总第 {issue+484} 期<br>每周三 08:00 推送</div>',
        '<div class="mh-center"><h1>AI · 汽车科技每周情报</h1><div class="sub">AI科技 · 车企动态 · 汽车AI技术 · 技术论文 · 行业总结</div></div>',
        '<div class="mh-right">关键词：情报<br>订阅：钉钉群推送</div>',
        "</header>",
        f'<div class="kp-bar">{kp_items}</div>',
        '<div class="main-grid">',
        # --- 左侧栏 ---
        '<div class="col col-left">',
        '<div class="sec-hdr"><span class="sec-num accent">01</span><div class="sec-rule" style="background:var(--accent);"></div><span class="sec-title accent">AI 圈 新 闻</span></div>',
        f'<div class="multi-col">{stories_html(data["ai_news"])}</div>',
        '<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num accent">06</span><div class="sec-rule" style="background:var(--accent);"></div><span class="sec-title accent">AI 圈 深 度</span></div>',
        f'<div class="multi-col">{stories_html(data["ai_deep"])}</div>',
        hbox_html("中央网信办：AI 面临五大安全风险", "技术先天脆弱性、模型失控、智能体自主行动、误用滥用及全球技术霸权五方面挑战，需加强治理与监管协作。", "blue"),
        '<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num gold">07</span><div class="sec-rule" style="background:var(--accent-gold);"></div><span class="sec-title gold">本 周 总 结</span></div>',
        f'<div class="multi-col">{summary_blocks}</div>',
        "</div>",
        # --- 中间栏 ---
        '<div class="col col-mid">',
        '<div class="sec-hdr"><span class="sec-num blue">02</span><div class="sec-rule" style="background:var(--accent-blue);"></div><span class="sec-title blue">车 企 科 技</span></div>',
        f'<div class="multi-col">{stories_html(data["auto_tech"])}</div>',
        '<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num gold">03</span><div class="sec-rule" style="background:var(--accent-gold);"></div><span class="sec-title gold">领 导 变 动</span></div>',
        f'<div class="multi-col">{leadership_blocks}</div>',
        '<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num green">04</span><div class="sec-rule" style="background:var(--accent-green);"></div><span class="sec-title green">汽 车 AI 技 术</span></div>',
        f'<div class="multi-col">{stories_html(data["auto_ai"])}</div>',
        "</div>",
        # --- 右侧栏 ---
        '<div class="col col-right">',
        '<div class="sec-hdr"><span class="sec-num purple">05</span><div class="sec-rule" style="background:var(--accent-purple);"></div><span class="sec-title purple">技 术 论 文</span></div>',
        f'<div class="multi-col">{paper_html(data["papers"])}</div>',
        '<div class="sec-hdr" style="margin-top:6px;"><span class="sec-num purple">&#9733;</span><div class="sec-rule" style="background:var(--accent-purple);"></div><span class="sec-title purple">GitHub 开 源</span></div>',
        f'<div class="multi-col">{gh_html(data["github"])}</div>',
        "</div>",
        "</div>",
        f'<footer class="footer"><span>&#128250; 本情报由 Mavis 每周自动抓取整理</span><span>每周三 08:00 定时推送至钉钉群</span><span>第 {issue} 期 · {date_str}</span></footer>',
        "</div>",
        "</body>",
        "</html>",
    ])


def main():
    html = build_html(NEWS_DATA)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] {OUTPUT_HTML} generated, {len(html)} chars")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(NEWS_DATA, f, ensure_ascii=False, indent=2)
    print(f"[OK] {OUTPUT_JSON} saved")
    today = datetime.now()
    issue = 36 + (today - datetime(2026, 9, 2)).days // 7
    print(f"Issue #{issue} | {today.strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    main()
