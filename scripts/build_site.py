#!/usr/bin/env python3
"""生成 docs/ 下的静态 HTML 站点。

用法：python3 scripts/build_site.py
依赖：Python 3 + `markdown`（pip install markdown）。
轮次报告原文在 rounds/roundNN/*.md，本脚本只做排版，不改动任何原始资料。
新增一轮时：把材料放进 rounds/roundNN/，在下面 ROUNDS 里加一条，再运行本脚本。
"""
import html
import json
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# ---------------------------------------------------------------- round metadata
ROUNDS = [
    dict(n=11, date="2026-10-07", md="rounds/round11/WENMI_ROUND11.md",
         title="原始资料入口复核 + 任意私人表恢复法的正对照失败",
         tags=["archive", "neg"],
         points=[
             "爱知大学馆藏目录 PDF 页图核实：1923-02-10 胡汉民→藤瀬政次郎书简，备注“孫中山との間の暗号電報，用法…”（仅目录，正文未得）。",
             "新算法：任意两字母→00–99 单射表 + 标准电码 + 语言模型退火。",
             "正对照失败：在 1917 年 3 月已解电报上，假明文得分高于真钥（−307 vs −381），只对上 1/51 个映射 → 该路线会制造“伪中文”。",
         ]),
    dict(n=12, date="2026-10-08", md="rounds/round12/WENMI_ROUND12.md",
         title="爱知大学实物展品影像与真实历史数字转换表",
         tags=["archive", "neg"],
         points=[
             "成功打开爱知大学纪念中心“広東政府首脳間で用いられた暗号電報”展品原图（山田纯三郎旧藏）。",
             "由展品 5 个样例（時機大可為）在 9600 种表中唯一恢复 20×5 数字表：辅音 xyzbcdfghjklmnpqrstv，元音 uoiea。",
             "冻结此表测六月：0509 有 5/35、0511 有 22/125 槽位不可识别，几乎全部含 y → 该表不能直接用于六月。",
             "发现展品下方另有 a/o/i/e/u/y 六行假名表，值得追查。",
         ]),
    dict(n=13, date="2026-10-09", md=None,
         title="（材料缺失）第64号表与 Kuzuoglu (2018) 全表核对",
         tags=["archive"],
         points=["据 Round 14 引述：Round 13 将爱知大学五码样例与 Kuzuoglu (2018) 印出的第64号 100 格表逐格核对一致。本仓库未收到 Round 13 的报告与 ZIP。"]),
    dict(n=14, date="2026-10-10", md="rounds/round14/WENMI_ROUND14.md",
         title="y 双角色的可复现结构检验",
         tags=["struct"],
         points=[
             "假设：a/e/i/o/u 只作元音，其它只作辅音，y 可兼两者，两字母组 CV/VC 皆可。",
             "0509 35/35、0511 124/125（含8字母词 140/141）合法；唯一例外 kohokycuee 的 ee。",
             "词内随机重排 10,000 次对照 p<0.0001；1916-04-03 汕头电报正对照 84/84。",
             "Kuzuoglu (2018) 指出 1913《仁密電碼本》等具名码本（党史馆 yiban050/5.3），“文密”可能也是具名私密本。",
         ]),
    dict(n=15, date="2026-10-11", md="rounds/round15/WENMI_ROUND15.md",
         title="找到戴季陶本人对 1917 年六月赴日任务的原版叙述",
         tags=["archive"],
         points=[
             "逐页核对 1928 民智书局《日本論》第103–108页：约6月16日离沪、21日抵东京，见秋山真之、田中义一。",
             "第108页：戴自述“当晚写成一封详尽的调查报告寄给总理” → 最有希望的同文/留底线索。",
             "定位台湾国家图书馆 1954 台北版（NCL-000001976），第71–72页仍未读到。",
             "时序张力：回忆称住三四天即返沪，但 0511 标为 6月29日东京发。",
         ]),
    dict(n=16, date="2026-10-12", md="rounds/round16/WENMI_ROUND16.md",
         title="首次目视核验六月电报扫描复制图，独立重读与4字母对齐",
         tags=["archive", "struct"],
         points=[
             "取得 Brice Dudout 公开的 0509 / 0511 JACAR 扫描复制图并逐张目视（图像不在本仓库再分发）。",
             "关键纠偏：六月两封电报并没有“文密”或“Cg”前缀；1916 的 G0/Y0 密钥均不能译出。",
             "Dudout 独立盲读：0509 为 8×10=80 字母；kohokycuee 实为 kohokycuce，原 ee 异常不再稳固。",
             "4 字母重合检查出现与词界不同步的重复结构（cafe、kige、mafy）。",
         ]),
    dict(n=17, date="2026-10-13", md="rounds/round17/WENMI_ROUND17.md",
         title="两枚三重重复码、页界相位与摩斯 ä 的穷举",
         tags=["struct"],
         points=[
             "相位 (0,0,2) 下 cafe 与 mupo 在 0509 / 0511a / 0511b 各出现一次；8 对重复、7 对跨段。",
             "词内重排对照 p≈2×10⁻⁵；1917 年 3 月已解电报作检测器正对照（p≈1.7×10⁻⁴）。",
             "0511 共 282 字母，模4余2，与“纯四字母=一汉字”不相容。",
             "摩斯 ä 可拆为 e+k / a+a / r+t 三种，前两种语法合法 → 不唯一。",
             "电报纸“Words: 32 / 14”与词数吻合，整词无缺失。",
         ]),
    dict(n=18, date="2026-10-14", md="rounds/round18/WENMI_ROUND18.md",
         title="元音开头音节是“虚码”——0511 恰为 67 个电码；扩大排除范围",
         tags=["struct", "neg"],
         points=[
             "删除 7 个元音开头的字母对（ac/as/op/um/ax…）后：0509=20 码，0511=67 码（40+27），长度完全自洽。",
             "辅音奇偶 z 从 4.1 升到 6.3；重复码对 11（随机删除对照 p≈0.0004）；统计形态与 1916 真实电报吻合。",
             "求解器在 1916 真实 Y0 密文上无先验找回原钥（正对照）；但六月在线性/5宽/Y0 同构/加数/坐标表等族全部阴性。",
             "唯一解距离：自由乱序表约需 88 码，而六月总共只有 87 码 → 仅凭这两封电报几乎不可解，需要新材料。",
         ]),
]

TAG_LABEL = {"struct": ("struct", "结构发现"), "archive": ("archive", "新档案/材料"),
             "neg": ("neg", "排除/负结果"), "block": ("block", "卡点")}

NAV = [("index.html", "首页"), ("blockers.html", "卡点与求助"), ("telegrams.html", "密电原文"),
       ("rounds.html", "研究轮次"), ("sources.html", "资料来源"),
       ("credits.html", "前人工作与致谢")]


def page(title, body, depth=0, active=""):
    up = "../" * depth
    nav = "".join(
        f'<a href="{up}{href}"{" class=on" if href == active else ""}>{label}</a>' for href, label in NAV)
    return f"""<!doctype html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · 孙戴1917六月密电</title>
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>
<header class="topbar"><div class="inner">
<a class="brand" href="{up}index.html"><span class="seal">密</span>sun-dai-1917-cipher</a>
<nav>{nav}</nav>
</div></header>
<main>
{body}
</main>
<footer>孙中山—戴季陶 1917 年六月密电 · 开放研究档案 · 维护者 <a href="https://x.com/MinliBuilds">X @MinliBuilds</a> · <a href="mailto:uslimin@gmail.com">uslimin@gmail.com</a> · <a href="https://github.com/limin112/sun-dai-1917-cipher">GitHub</a><br>文字、数据与代码 CC BY 4.0 · 电报扫描图出自 JACAR（日本外务省外交史料馆藏），不在 CC BY 范围内</footer>
</body>
</html>
"""


def tags_html(tags):
    return "".join(f'<span class="tag {TAG_LABEL[t][0]}">{TAG_LABEL[t][1]}</span>' for t in tags)


def md_to_html(text):
    return markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])


# ---------------------------------------------------------------- round pages
def build_rounds():
    out = DOCS / "rounds"
    out.mkdir(parents=True, exist_ok=True)
    for i, r in enumerate(ROUNDS):
        n = r["n"]
        summary = "".join(f"<li>{html.escape(p)}</li>" for p in r["points"])
        files_html = ""
        if r["md"]:
            rdir = ROOT / Path(r["md"]).parent
            files = sorted(p.relative_to(rdir).as_posix() for p in rdir.rglob("*") if p.is_file())
            rel = f"../../{Path(r['md']).parent.as_posix()}/"
            files_html = "<h2>本轮材料（原样归档）</h2><ul class=files>" + "".join(
                f'<li><a href="{rel}{f}">{html.escape(f)}</a></li>' for f in files) + "</ul>"
            report = md_to_html((ROOT / r["md"]).read_text(encoding="utf-8"))
            report = re.sub(r"^<h1>.*?</h1>", "", report, count=1, flags=re.S)
        else:
            report = "<blockquote>本轮的报告与复现包未包含在交接材料中。如你持有 Round 13 的 WENMI_ROUND13.md / sun_wenmi_round13.zip，欢迎提交 PR。</blockquote>"
        prev_link = (f'<a href="round-{ROUNDS[i-1]["n"]}.html">← Round {ROUNDS[i-1]["n"]}</a>'
                     if i > 0 else "<span></span>")
        next_link = (f'<a href="round-{ROUNDS[i+1]["n"]}.html">Round {ROUNDS[i+1]["n"]} →</a>'
                     if i + 1 < len(ROUNDS) else "<span></span>")
        body = f"""<div class="narrow">
<div class="kicker">Round {n} · {r['date']}</div>
<h1>{html.escape(r['title'])}</h1>
<div>{tags_html(r['tags'])}</div>
<section class="summary"><h2>本轮要点</h2><ul>{summary}</ul>
<div class="meta">六月电报已验证译文仍为 0 字。以下为原始报告全文，结论以更高轮次为准。</div></section>
<h2>报告全文</h2>
{report}
{files_html}
<div class="pager">{prev_link}<a href="../rounds.html">全部轮次</a>{next_link}</div>
</div>"""
        (out / f"round-{n}.html").write_text(page(f"Round {n}", body, depth=1, active="rounds.html"),
                                             encoding="utf-8")


def timeline_html(depth=0):
    up = "../" * depth
    items = []
    for r in reversed(ROUNDS):
        cls = "" if r["md"] else ' class="missing"'
        items.append(f"""<li{cls}><div class="date">ROUND {r['n']} · {r['date']}</div>
<div class="title"><a href="{up}rounds/round-{r['n']}.html">{html.escape(r['title'])}</a></div>
<div>{tags_html(r['tags'])}</div><p>{html.escape(r['points'][0])}</p></li>""")
    return '<ol class="timeline">' + "".join(items) + "</ol>"


def build_rounds_index():
    body = f"""<div class="narrow">
<div class="kicker">Research log</div>
<h1>研究轮次</h1>
<p class="lede">每一轮都附原始报告、代码、输入 SHA、正/负对照与运行日志。后面的轮次可能推翻前面的疑读或暂定结构，请以高轮次为准。Round 1–10 未纳入本次整理（相关结论已被 11–18 轮继承或推翻）。</p>
{timeline_html()}
</div>"""
    (DOCS / "rounds.html").write_text(page("研究轮次", body, active="rounds.html"), encoding="utf-8")


# ---------------------------------------------------------------- telegrams page
STREAM_B = {
    "0509（1917-06-24 孙→戴，20 码）":
        "lida jysa myve muce kyri meve cafe mupo kelu tazi riye cafa ficy mefy meca mada mymi ripu jiho kehe",
    "0511a（1917-06-29 戴→孙，第1页 40 码）":
        "mupo yobe myzo doke cate jido keyo kige leyi liri duri cidu leko hoky cuce kuxo mifu muhu tady nygo "
        "capa kazu yemy cyka fevu damo hosy cydi capa yobe nyzo hinu cuge rify jabo mahy kagi cafe gaji riby",
    "0511b（第2页 27 码）":
        "jomo fojy micy cote cofu hodi jige cafe migy mupo kyce kige rudu byri jojo rini mafy fojy lisi bymi "
        "kypo mice miya mino mafy kazo kipa",
}
REPEATS = ["cafe", "mupo", "yobe", "kige", "capa", "fojy", "mafy"]


def tele_block(label, words, highlight=None, unc=()):
    spans = []
    for w in words.split():
        if highlight and w in highlight:
            spans.append(f'<mark class="r{highlight.index(w) + 1}">{w}</mark>')
        elif w in unc:
            spans.append(f'<span class="unc">{w}</span>')
        else:
            spans.append(w)
    return f'<div class="tele"><span class="label">{html.escape(label)}</span>{" ".join(spans)}</div>'


def build_telegrams():
    ct = json.loads((ROOT / "data/ciphertexts.json").read_text(encoding="utf-8"))
    wit = json.loads((ROOT / "data/independent_witness.json").read_text(encoding="utf-8"))
    raw = ct["raw_june_notes"]
    unc = {"vemucayri", "mevecafema(u)", "kohokycuee", "hutadyny(y)go", "rifyjabo(?)", "damoumhosy",
           "vemucicyri", "muposacyobe", "catyidohe", "damowmhosy", "kohokycuce", "fogylisicy"}
    raw_blocks = "".join(tele_block(k, v, unc=unc) for k, v in raw.items())
    wit_blocks = ""
    for k, v in wit["telegrams"].items():
        words = v["words"]
        segs = v["segments"]
        if len(segs) == 2:
            wit_blocks += tele_block(f"{k} 第1页（{segs[0]} 词）", " ".join(words[:segs[0]]), unc=unc)
            wit_blocks += tele_block(f"{k} 第2页（{segs[1]} 词）", " ".join(words[segs[0]:]), unc=unc)
        else:
            wit_blocks += tele_block(f"{k}（{segs[0]} 词）", " ".join(words), unc=unc)
    stream = "".join(tele_block(k, v, highlight=REPEATS) for k, v in STREAM_B.items())
    body = f"""<div class="narrow">
<div class="kicker">The ciphertexts</div>
<h1>密电原文与读本</h1>
<p class="lede">目标：日本亚洲历史资料中心（JACAR）<b>B03050090200</b> 帧 <b>0509</b>（1917-06-24，孙中山 上海 → 戴季陶 东京，署名 <code>Sunwen</code>）与帧 <b>0511</b>（1917-06-29，戴季陶 东京 → 孙中山 上海，两张电报纸，署名 <code>Tai</code>）。</p>
<h2>电报扫描图</h2>
<div class="scans">
<figure><a href="assets/img/jacar/scan-0509-full.webp"><img src="assets/img/jacar/scan-0509-full.webp" alt="JACAR B03050090200 帧0509，1917-06-24 上海发东京电报" loading="lazy"></a>
<figcaption>帧 0509 · 1917-06-24 上海发，6-25 东京收 · 署名 Sunwen · Words 14</figcaption></figure>
<figure><a href="assets/img/jacar/scan-0511-full.webp"><img src="assets/img/jacar/scan-0511-full.webp" alt="JACAR B03050090200 帧0511，1917-06-29 东京发上海电报，两页" loading="lazy"></a>
<figcaption>帧 0511 · 1917-06-29 东京发上海 · 两张电报纸 · 署名 Tai · Words 32</figcaption></figure>
</div>
<blockquote>出处：日本外务省外交史料馆藏，亚洲历史资料中心（JACAR）提供，Ref. <a href="https://www.jacar.archives.go.jp/das/meta/B03050090200">B03050090200</a>。
本仓库中的副本取自 Brice Dudout 公开的 <a href="https://github.com/bdudout/wenmi">wenmi</a> 项目（Git blob SHA 与研究记录一致），<b>不在本仓库 CC BY 4.0 授权范围内</b>，使用请遵循 JACAR 利用规定。点击可看大图。
下文黄底 = 已知存在争议的读法。</blockquote>

<h2>读本 1：Bourdeau 原始转录（raw，冻结不改）</h2>
<p>来源：<a href="https://github.com/dbourdeau/cyphersolver/blob/main/targets/sunyatsen/y1917/NOTES.md">dbourdeau/cyphersolver</a>，冻结于 <a href="../data/ciphertexts.json">data/ciphertexts.json</a>。</p>
{raw_blocks}

<h2>读本 2：Dudout 独立盲读（witness）</h2>
<p>来源：<a href="{wit['source_url']}">bdudout/wenmi</a>（CC BY 4.0），冻结于 <a href="../data/independent_witness.json">data/independent_witness.json</a>。不是唯一核定原文。</p>
{wit_blocks}

<h2>Round 18 解析：删除元音开头虚码后的四字母电码流</h2>
<p>同色下划线 = 重复电码（cafe×3、mupo×3、yobe、kige、capa、fojy、mafy 各×2）。这是<b>结构假设</b>，不是译文；重复的 <code>yobe myzo</code> 双码是将来做已知明文攻击的首选位置。</p>
{stream}

<h2>已知的字符级疑点</h2>
<table>
<tr><th>位置</th><th>候选读法</th><th>状态</th></tr>
<tr><td>0509 第2词</td><td><code>vemucäyri</code>（摩斯 ä）→ <code>vemucekyri</code> / <code>vemucaayri</code> / <code>vemucrtyri</code>；独立视觉读 <code>vemucicyri</code></td><td>未定（R17）</td></tr>
<tr><td>0509 第3词</td><td><code>mevecafema(u)</code> / <code>mevecafemu</code></td><td>R16 倾向 10 字母</td></tr>
<tr><td>0511 第1词</td><td><code>mukoacyobe</code> / <code>muposacyobe</code>（11字母）</td><td>未定</td></tr>
<tr><td>0511 第3词</td><td><code>catejidoke</code> / <code>catyidohe</code>（9字母）</td><td>未定</td></tr>
<tr><td>0511 第7词</td><td><code>kohokycuee</code> / <code>kohokycuce</code></td><td>R18 唯一强负相位词，重点复核</td></tr>
<tr><td>0511 第9词</td><td><code>hutadyny(y)go</code> / <code>hutadynyfo</code></td><td>未定</td></tr>
<tr><td>0511 第12词</td><td><code>damoumhosy</code> / <code>damowmhosy</code></td><td>未定</td></tr>
<tr><td>0511 页界</td><td>第1页末 / 第2页首是否漏、增一组</td><td>R18 虚码解析后不再需要</td></tr>
</table>
</div>"""
    (DOCS / "telegrams.html").write_text(page("密电原文", body, active="telegrams.html"), encoding="utf-8")


# ---------------------------------------------------------------- sources page
def build_sources():
    src = md_to_html((ROOT / "handoff/SOURCES_AND_ACCESS.md").read_text(encoding="utf-8"))
    src = re.sub(r"^<h1>.*?</h1>", "", src, count=1, flags=re.S)
    src = re.sub(r"(?<![\"'>])(https?://[^\s<，、）)]+)", r'<a href="\1">\1</a>', src)
    body = f"""<div class="narrow">
<div class="kicker">Sources &amp; access</div>
<h1>资料来源与访问记录</h1>
<p class="lede">区分“已取得并核验”“仅定位到目录/馆藏号”“访问失败”。档号 ≠ 已获取扫描；重复的 DNS/403 失败不算进展。</p>
{src}
<h2>各轮引用的其他材料</h2>
<table>
<tr><th>材料</th><th>状态</th><th>轮次</th></tr>
<tr><td>爱知大学纪念中心展品“広東政府首脳間で用いられた暗号電報”<br><a href="https://edu.aichi-u.ac.jp/toa/collection/gallery02/Com1000075.html">展品页</a></td><td>官方图已目视；不转载</td><td>R12</td></tr>
<tr><td>Kuzuoglu (2018), <i>Chinese cryptography</i>, Cryptologia, <a href="https://doi.org/10.1080/01611194.2018.1449146">doi:10.1080/01611194.2018.1449146</a></td><td>第64号 100 格表已核对</td><td>R13–R14</td></tr>
<tr><td>戴季陶《日本論》1928 民智书局本（<a href="https://commons.wikimedia.org/wiki/File:NLC416-03jh003405-24940_日本論.pdf">Wikimedia Commons</a>）第103–108页</td><td>已逐页目视</td><td>R15</td></tr>
<tr><td>《日本論》1954 台北中央文物供应社版（<a href="https://taiwanebook.ncl.edu.tw/*/book/NCL-000001976">NCL-000001976</a>）第71–72页</td><td>已定位，未读到</td><td>R15</td></tr>
<tr><td>Brice Dudout / Claude「破解文密」 <a href="https://bdudout.github.io/wenmi/">项目主页</a> · <a href="https://bdudout.github.io/wenmi/zh-hans/method.html">技术报告</a></td><td>扫描复制图、盲读转录、lm3 语言模型（CC BY 4.0）</td><td>R16–R18</td></tr>
<tr><td>Cryptiana 关于该展品的讨论（<a href="https://github.com/NoAutopilot/cipher-lab/blob/main/sources/cryptiana/web/chinesecrypto_e.htm">镜像</a>）</td><td>前人研究</td><td>R12</td></tr>
</table>
</div>"""
    (DOCS / "sources.html").write_text(page("资料来源", body, active="sources.html"), encoding="utf-8")


# ---------------------------------------------------------------- blockers (卡点)
BLOCKERS = [
    ("同钥匙的更多密文",
     "唯一解距离估计：自由乱序表约需 88 码，而六月两封总共 87 码。仅凭这两封，统计搜索几乎不可能得到可验收的译文。",
     ["JACAR《特定人ノ発受郵便物取調》第四卷之后的卷册；",
      "1917 年 7–9 月孙中山在广州期间与东京之间的电报——凡含元音开头虚码或 y 作元音的六元音电报都应纳入；",
      "哪怕再多 100–200 码，自由表也可能进入可解区。"],
     "直接把问题从“不可解”拉进“可解”区间。"),
    ("中文侧同文 / 留底（已知明文）",
     "戴季陶《日本論》自述 6 月抵东京当晚写了详尽调查报告寄给孙中山，但报告原件未找到。",
     ["《國父年譜》下册第926页（派戴傳賢赴日調查復辟運動）；",
      "《日本論》1954 台北中央文物供应社版第71–72页（台湾国家图书馆 NCL-000001976，PDF 读取失败）；",
      "《孙中山全集》1917 年 6 月致戴季陶函电；秋山真之、田中义一档案中的相关记录。"],
     "若能确认任一段原文，即可得到大量音节锚点，做已知明文攻击。"),
    ("具名私人码本实物",
     "1913《仁密電碼本》等具名码本说明“文密”可能也是一部私人重编码本；若是，必须找到码本本身。",
     ["国民党党史馆档案（<a href=\"https://archiveds.lib.nccu.edu.tw/\">政大档案探索系统</a>）：一般档案 <code>yiban050/5.3</code>（仁密）、<code>yiban333/2.2</code>（第64号）、<code>yiban050/1.2</code>（1918 日文密码），尤其凡例、附表、页眉私填数字、换密条；",
      "爱知大学孙文—山田纯三郎资料：1923-02-10 胡汉民致藤瀬政次郎书简（目录 270 / 整理 138 / 24-6，备注“孫中山との間の暗号電報，用法，時間，場所の説明”），微缩胶片在丰桥校区图书馆；",
      "爱知大学展品下方 a/o/i/e/u/y 六行假名表的高清扫描与年代说明。"],
     "拿到真表后可直接做受约束解码 + 逐字重加密验收。"),
    ("时序问题",
     "戴季陶回忆约 6 月 21 日到东京、住三四天后返沪；但 0511 标注 6 月 29 日东京发。",
     ["核对 0511 电报纸上的发报局、日期戳与 JACAR 目录著录；",
      "查戴季陶 1917 年 6 月下旬的行程记录（船期、报纸报道）。"],
     "关系到 0511 的发报人与内容背景判断。"),
]


def build_blockers():
    items = ""
    for i, (title, why, asks, unlock) in enumerate(BLOCKERS, 1):
        lis = "".join(f"<li>{a}</li>" for a in asks)
        items += f"""<div class="blocker"><div class="num">{i:02d}</div><div>
<h3>{title}</h3><p>{why}</p><ul>{lis}</ul><p class="unlock">↳ 价值：{unlock}</p></div></div>"""
    body = f"""<div class="narrow">
<div class="kicker">Where we are stuck · Help wanted</div>
<h1>卡点与求助</h1>
<p class="lede">经过 18 轮，结构层面已经有可复现的信号（虚码切分、67+20 个电码、11 个重复码对），也排除了大批规则表族。
但定量估计显示：<b>只靠现有这 87 个电码，几乎不可能解出</b>。真正缺的是新材料，而不是更多统计搜索。如果你能接触下列任一资料，欢迎提 <a href="https://github.com/limin112/sun-dai-1917-cipher/issues">Issue</a> / PR，或联系 <a href="https://x.com/MinliBuilds">X @MinliBuilds</a>、<a href="mailto:uslimin@gmail.com">uslimin@gmail.com</a>。</p>
{items}
<h2>验收标准（怎样才算“破译”）</h2>
<p>只有同时满足以下全部条件，才称得到中文译文；单向解码、语言模型通顺、显著的随机对照、任意字母换名都不够：</p>
<ol>
<li>确切码本实物，或特定书籍版次 / 表格规则；</li>
<li>所有异常字符都有原图依据和完整校改日志；</li>
<li>每个字 / 控制码都能从译文逐位重加密回冻结密文；</li>
<li>有未用于拟合的独立同钥电报或同文明文留底作交叉验证；</li>
<li>所有中间文件、负结果、校验记录完整公开。</li>
</ol>
<h2>已经排除的路线（不必再重复）</h2>
<ul>
<li>任意两字母→00–99 单射表 + 语言模型盲搜（R11：正对照失败，会制造伪中文）；</li>
<li>爱知大学展品 / 第64号 20×5 表原样套用（R12）；</li>
<li>1916 G0 / Y0、1917 年 3 月已解密钥（R16）；</li>
<li>6 宽线性表任意辅音序 / 元音序 / 蛇形 / 偏移 0–99；5 宽 + y 同码异形；Y0 同构 97,920 把；首音节千位数字排列 × 加数；一般整码加法（0000–9999）；双表共序；G0 式 6 元音坐标表（R18）。</li>
</ul>
</div>"""
    (DOCS / "blockers.html").write_text(page("卡点与求助", body, active="blockers.html"), encoding="utf-8")


def build_index():
    body = f"""<section class="hero">
<div>
<div class="kicker">Open research archive</div>
<h1>孙中山—戴季陶<br>1917 年六月密电</h1>
<p class="lede">日本外务省档案（JACAR B03050090200）中有两封 1917 年 6 月孙中山与戴季陶之间的拉丁字母密电，至今无人破译。
这里公开我们 11–18 轮研究的全部报告、代码、数据、正负对照与失败记录——以及我们卡在哪里。</p>
<p><a href="blockers.html"><b>→ 我们卡在哪里，需要什么帮助</b></a></p>
<p style="font-size:14px;color:var(--ink-2)">维护者 <a href="https://x.com/MinliBuilds">X @MinliBuilds</a> · <a href="mailto:uslimin@gmail.com">uslimin@gmail.com</a></p>
</div>
<div class="status-card">
<div class="kicker">当前状态 · 2026-10-14 · Round 18</div>
<div class="big">0 字</div>
<div>六月电报已验证中文译文</div>
<dl>
<dt>密钥 / 码本</dt><dd>未找到</dd>
<dt>电码结构</dt><dd>0509 = 20 码；0511 = 67 码（40+27）</dd>
<dt>最强结构信号</dt><dd>虚码切分后辅音奇偶 z≈6.3，重复码对 11</dd>
<dt>主要瓶颈</dt><dd>密文太少（87 码 &lt; 唯一解距离 ≈88 码）</dd>
</dl>
</div>
</section>

<h2>两封电报</h2>
<div class="grid">
<div class="card"><h3>帧 0509 · 1917-06-24</h3><p>孙中山（上海）→ 戴季陶（东京）。8 个 10 字母密文词，署名 Sunwen。张勋复辟前夕，孙派戴赴日了解日本军政界态度。</p></div>
<div class="card"><h3>帧 0511 · 1917-06-29</h3><p>戴季陶（东京）→ 孙中山（上海）。两张电报纸，29 个密文词（282 字母），署名 Tai。</p></div>
<div class="card"><h3>不是“文密”</h3><p>两封电报并无“文密”或“Cg”前缀，1916 年已破的 G0/Y0 密钥与 1917 年 3 月密钥均无法译出。</p></div>
<div class="card"><h3>前人工作</h3><p>Daniel Bourdeau（1917 年 3 月电报已解）、Brice Dudout / Claude（1916 文密 G0/Y0 已解、扫描复制图与盲读）。<a href="credits.html">详见致谢 →</a></p></div>
</div>
<p><a href="telegrams.html">查看全部密文读本与 Round 18 电码流 →</a></p>

<h2>研究时间线</h2>
{timeline_html()}

<h2>如何使用这个仓库</h2>
<ul>
<li><code>rounds/roundNN/</code>：每一轮的原始报告、脚本、输入、结果与 <code>MANIFEST.sha256</code>，原样归档；</li>
<li><code>data/</code>：最新冻结输入（原始转录、独立盲读、摩斯与页面观察、三月正对照、R18 结构结果）；</li>
<li><code>handoff/</code>：给下一位研究者 / Agent 的交接文档与任务卡；</li>
<li><code>docs/</code>：本站点，由 <code>python3 scripts/build_site.py</code> 生成。</li>
</ul>
"""
    (DOCS / "index.html").write_text(page("首页", body, active="index.html"), encoding="utf-8")


# ---------------------------------------------------------------- credits
CREDITS = [
    dict(name="Daniel Bourdeau · cyphersolver",
         url="https://github.com/dbourdeau/cyphersolver",
         site="https://dbourdeau.github.io/cyphersolver/sunintercepts.html",
         license="文字与笔记 CC BY 4.0；代码 MIT",
         since="早于 Round 11（Round 1–10 不在本仓库，确切起点待补）",
         used=[
             "六月两封密电的原始转录（<code>targets/sunyatsen/y1917/NOTES.md</code>、<code>fam6.py</code>），是 <a href=\"../data/ciphertexts.json\">data/ciphertexts.json</a> 的底本；",
             "1916 年已解电报转录 <code>targets/sunyatsen/y1916/transcripts_A–D.md</code>，Round 11 用来训练语言评分器；",
             "1917 年 3 月 23/25/26 日已破译电报与密钥（<code>show17.py</code>、<code>fam17.py</code>），作为算法正对照（Round 11、17），从不参与六月拟合；",
             "20×5 表旋转 / 反转 / 元音列变换的系统化枚举思路。",
         ]),
    dict(name="Brice Dudout（与 Claude 合作）· wenmi「破解文密」",
         url="https://github.com/bdudout/wenmi",
         site="https://bdudout.github.io/wenmi/",
         license="CC BY 4.0（JACAR 扫描图除外）",
         since="Round 16",
         used=[
             "帧 0509 / 0511 扫描复制图——本研究第一次看到六月原件，本仓库 <code>docs/assets/img/jacar/</code> 的两张图即取自该项目；",
             "独立盲读转录 <a href=\"../data/independent_witness.json\">data/independent_witness.json</a>，Round 16–18 所有结构结论都在两份读本上分别验证；",
             "关键纠偏：六月电报无“文密”/“Cg”前缀，1916 G0/Y0 密钥译不出；",
             "<code>solver/lm3</code> 语言模型与 1916 Y0/G0 真实数据，Round 18 求解器与正对照依赖它；",
             "元音开头字母对的“颠倒”观察——Round 18 的“虚码”解析即由此出发。",
         ]),
    dict(name="Cryptiana（经 NoAutopilot/cipher-lab 镜像）",
         url="https://github.com/NoAutopilot/cipher-lab/blob/main/sources/cryptiana/web/chinesecrypto_e.htm",
         site="", license="见原站",
         since="Round 12",
         used=["对爱知大学展品“広東政府首脳間で用いられた暗号電報”及其样例、底部假名转换表的早期讨论；Round 12 据此说明该展品并非本项目首次发现。"]),
]

INSTITUTIONS = [
    ("亚洲历史资料中心（JACAR）/ 日本外务省外交史料馆", "目标电报原件 B03050090200；1916 年对照件 B03050090000。", "https://www.jacar.archives.go.jp/"),
    ("爱知大学东亚同文书院大学纪念中心", "山田纯三郎旧藏密码电报展品、孙文—山田资料馆藏目录（Round 11–12）。", "https://edu.aichi-u.ac.jp/toa/collection/gallery02/Com1000075.html"),
    ("Kuzuoglu, Ulug (2018). Chinese cryptography. Cryptologia", "第64号 20×5 表全文、1913《仁密電碼本》等具名码本线索（Round 13–14）。", "https://doi.org/10.1080/01611194.2018.1449146"),
    ("中国国家图书馆 / Wikimedia Commons", "戴季陶《日本論》1928 民智书局本扫描（Round 15）。", "https://commons.wikimedia.org/wiki/File:NLC416-03jh003405-24940_日本論.pdf"),
    ("台湾国家图书馆·臺灣華文電子書庫", "《日本論》1954 台北版馆藏著录 NCL-000001976（Round 15）。", "https://taiwanebook.ncl.edu.tw/*/book/NCL-000001976"),
    ("国立政治大学·国民党党史档案探索系统", "仁密、第64号、1918 日文密码等档号定位（待取得）。", "https://archiveds.lib.nccu.edu.tw/"),
]


def build_credits():
    cards = ""
    for c in CREDITS:
        lis = "".join(f"<li>{u}</li>" for u in c["used"])
        site = f' · <a href="{c["site"]}">网站</a>' if c["site"] else ""
        cards += f"""<div class="blocker" style="grid-template-columns:1fr"><div>
<h3><a href="{c['url']}">{html.escape(c['name'])}</a>{site}</h3>
<p><span class="tag archive">授权：{html.escape(c['license'])}</span><span class="tag struct">引入：{html.escape(c['since'])}</span></p>
<ul>{lis}</ul></div></div>"""
    inst = "".join(f'<tr><td><a href="{u}">{html.escape(n)}</a></td><td>{html.escape(d)}</td></tr>'
                   for n, d, u in INSTITUTIONS)
    body = f"""<div class="narrow">
<div class="kicker">Prior work &amp; acknowledgements</div>
<h1>前人工作与致谢</h1>
<p class="lede">这个项目站在别人的肩膀上。六月电报的转录、1916 年与 1917 年 3 月的已解案例、扫描图和语言模型，都来自下面这些公开研究。
我们自己的贡献是在其上做的结构检验、排除搜索与资料追查——全部记录在 <a href="rounds.html">研究轮次</a> 中。</p>

<h2>开源研究仓库</h2>
{cards}

<h2>档案馆、文献与机构</h2>
<table><tr><th>来源</th><th>用途</th></tr>{inst}</table>

<h2>本仓库的授权</h2>
<ul>
<li>本仓库的文字、数据与代码采用 <a href="https://creativecommons.org/licenses/by/4.0/deed.zh-hans">CC BY 4.0</a>，与 wenmi 及 cyphersolver 的文字部分一致。引用请注明“sun-dai-1917-cipher contributors”并链接 <a href="https://github.com/limin112/sun-dai-1917-cipher">github.com/limin112/sun-dai-1917-cipher</a>。</li>
<li>源自上述仓库的转录与数据，在各文件中保留原作者署名，并按 CC BY 4.0 再分发。</li>
<li><b>不在 CC BY 范围内</b>：<code>docs/assets/img/jacar/</code> 的两张电报扫描图（日本外务省外交史料馆藏，JACAR 提供，注明出处转载，请遵循 JACAR 利用规定）；爱知大学展品照片未收录。</li>
</ul>

<h2>联系</h2>
<p>维护者：<a href="https://x.com/MinliBuilds">X @MinliBuilds</a> · <a href="mailto:uslimin@gmail.com">uslimin@gmail.com</a>。有新材料、更正或想法，欢迎联系或在 <a href="https://github.com/limin112/sun-dai-1917-cipher/issues">GitHub Issues</a> 讨论。</p>

<h2>研究方式说明</h2>
<p>各轮研究大量借助 AI Agent（Claude 等）完成。所有结论附脚本、输入 SHA、正负对照与运行日志，可独立复现；任何“通顺的中文”在通过验收标准前都不算译文。</p>
</div>"""
    (DOCS / "credits.html").write_text(page("前人工作与致谢", body, active="credits.html"), encoding="utf-8")


if __name__ == "__main__":
    build_rounds()
    build_rounds_index()
    build_telegrams()
    build_sources()
    build_blockers()
    build_index()
    build_credits()
    print("built", sorted(p.relative_to(ROOT).as_posix() for p in DOCS.rglob("*.html")))
