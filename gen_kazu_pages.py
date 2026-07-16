# -*- coding: utf-8 -*-
"""数意ページ生成スクリプト
js/fortune-meanings.js の NUMBER_MEANINGS から
kazu/index.html（一覧ハブ）と kazu/1〜81/index.html（個別解説）と sitemap.xml を生成する。
使い方: python gen_kazu_pages.py
"""
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
SITE = "https://m-a-asan.github.io/seimei-kantei"
TODAY = "2026-07-16"
BEACON = "<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{\"token\": \"9961ede6882241fb98504c8c4b8fc963\"}'></script><!-- End Cloudflare Web Analytics -->"

RANK_CLASS = {"大吉": "rank-great", "吉": "rank-good", "半吉": "rank-normal", "要注意": "rank-caution", "凶": "rank-hard"}

KAKU_HINTS = [
    ("天格", "姓（苗字）の画数から算出される、先祖から受け継ぐ家系の土台。天格が{n}画の場合、家系そのものに「{title}」の気質が流れていると読みます。天格は単独では吉凶を強く取らず、人格との組み合わせで見るのが基本です。"),
    ("人格", "姓の最後の文字と名の最初の文字を足した、性格と対人関係の中心。人格が{n}画の人は、内面の核に「{title}」の性質を最も強く帯びるとされ、五格の中でも特に重要視されます。"),
    ("地格", "名（下の名前）の画数から算出される、幼少期から青年期の運勢。地格が{n}画なら、人生の前半戦や物事の立ち上がりに{rank}の「{title}」の色合いが表れると読みます。"),
    ("外格", "総格から人格を引いた、社会からどう見られるかを表す数。外格が{n}画の人は、周囲からは「{title}」の印象で受け取られやすいとされます。"),
    ("総格", "姓名すべての画数の合計で、人生全体・特に晩年運を表す総合指標。総格{n}画は「{title}」——人生の集大成がこの数意のトーンに近づいていくと読む、最も重視される格です。"),
]

HEAD_COMMON = """<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="{css}">
<style>
.kazu-hero{{text-align:center;padding:18px 0 6px}}
.kazu-hero .num-seal{{display:inline-flex;flex-direction:column;align-items:center;justify-content:center;width:110px;height:110px;border:3px solid var(--vermillion);border-radius:14px;color:var(--vermillion);font-weight:700;background:#fff}}
.kazu-hero .num-seal b{{font-size:44px;line-height:1}}
.kazu-hero .num-seal span{{font-size:12px;margin-top:4px}}
.rank-chip{{display:inline-block;padding:3px 14px;border-radius:100px;color:#fff;font-size:13px;font-weight:700;margin:12px 0 4px}}
.rank-chip.rank-great{{background:var(--great)}}.rank-chip.rank-good{{background:var(--good)}}.rank-chip.rank-normal{{background:var(--normal)}}.rank-chip.rank-caution{{background:var(--caution)}}.rank-chip.rank-hard{{background:var(--hard)}}
.kazu-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:14px}}
.kazu-cell{{border:1px solid var(--line);border-radius:10px;padding:10px 12px;text-decoration:none;color:inherit;background:#fff;transition:.15s}}
.kazu-cell:hover{{border-color:var(--vermillion);transform:translateY(-2px)}}
.kazu-cell .kn{{font-weight:700;font-size:17px}}
.kazu-cell .kr{{font-size:11.5px;font-weight:700}}
.kazu-cell .kt{{font-size:12px;color:var(--ink-soft)}}
.kr.rank-great{{color:var(--great)}}.kr.rank-good{{color:var(--good)}}.kr.rank-normal{{color:var(--normal)}}.kr.rank-caution{{color:var(--caution)}}.kr.rank-hard{{color:var(--hard)}}
.kazu-nav{{display:flex;justify-content:space-between;gap:10px;margin:22px 0}}
.kazu-nav a{{flex:1;text-align:center;border:1px solid var(--line);border-radius:10px;padding:10px;text-decoration:none;color:inherit;font-size:14px}}
.kazu-nav a:hover{{border-color:var(--vermillion)}}
.same-rank{{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}}
.same-rank a{{border:1px solid var(--line);border-radius:100px;padding:4px 12px;font-size:13px;text-decoration:none;color:inherit}}
.same-rank a:hover{{border-color:var(--vermillion);color:var(--vermillion)}}
.kazu-cta{{text-align:center;margin:30px 0 6px}}
.kazu-cta .btn-primary{{display:inline-block;text-decoration:none;padding:14px 30px}}
.crumb{{font-size:12px;color:var(--ink-soft);margin-bottom:10px}}.crumb a{{color:inherit}}
</style>"""


def parse_meanings():
    src = (BASE / "js" / "fortune-meanings.js").read_text(encoding="utf-8")
    pat = re.compile(r'(\d+):\s*\{\s*rank:\s*FORTUNE_RANK\.(\w+),\s*title:\s*"([^"]+)",\s*text:\s*"([^"]+)"\s*\}')
    rank_map = {"GREAT": "大吉", "GOOD": "吉", "NORMAL": "半吉", "CAUTION": "要注意", "HARD": "凶"}
    out = {}
    for m in pat.finditer(src):
        out[int(m.group(1))] = {"rank": rank_map[m.group(2)], "title": m.group(3), "text": m.group(4)}
    return out


def page_for(n, m, meanings):
    rank, title, text = m["rank"], m["title"], m["text"]
    rc = RANK_CLASS[rank]
    prev_n, next_n = (n - 1 if n > 1 else 81), (n + 1 if n < 81 else 1)
    same = [k for k, v in sorted(meanings.items()) if v["rank"] == rank and k != n]
    same_links = "".join(f'<a href="../{k}/">{k}画</a>' for k in same)
    hints = "".join(
        f'<div class="guide-item"><h4>{kaku}に{n}画がある場合</h4><p>{tpl.format(n=n, title=title, rank=rank)}</p></div>'
        for kaku, tpl in KAKU_HINTS
    )
    ld = f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
{{"@type":"ListItem","position":1,"name":"姓名鑑定処","item":"{SITE}/"}},
{{"@type":"ListItem","position":2,"name":"画数の意味一覧","item":"{SITE}/kazu/"}},
{{"@type":"ListItem","position":3,"name":"{n}画の意味","item":"{SITE}/kazu/{n}/"}}]}}
</script>'''
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
{HEAD_COMMON.format(css="../../css/style.css?v=20260716")}
<title>姓名判断で{n}画の意味は「{title}」（{rank}）｜画数の数意解説 - 姓名鑑定処</title>
<meta name="description" content="姓名判断における{n}画は「{title}」（{rank}）。{text[:60]}——天格・人格・地格・外格・総格それぞれに{n}画が出た場合の読み方を解説します。">
<link rel="canonical" href="{SITE}/kazu/{n}/">
<meta property="og:type" content="article">
<meta property="og:title" content="姓名判断で{n}画の意味は「{title}」（{rank}）">
<meta property="og:site_name" content="姓名鑑定処">
{ld}
</head>
<body>
  <div class="wrap">
    <header class="site-header">
      <div class="brand-seal">鑑定</div>
      <h1 class="site-title">姓名鑑定処<small>SEIMEI KANTEI-DOKORO</small></h1>
    </header>
    <main>
      <div class="crumb"><a href="../../">姓名鑑定処</a> ／ <a href="../">画数の意味一覧</a> ／ {n}画</div>
      <section class="section-block">
        <div class="kazu-hero">
          <div class="num-seal"><b>{n}</b><span>画</span></div>
          <div><span class="rank-chip {rc}">{rank}</span></div>
          <h2 class="section-title">{n}画「{title}」の意味</h2>
        </div>
        <p class="intro-lead">{text}</p>
      </section>

      <section class="section-block">
        <h2 class="section-title">五格それぞれに{n}画が出たときの読み方</h2>
        <div class="guide-grid">
          {hints}
        </div>
      </section>

      <div class="kazu-cta">
        <a class="btn-primary" href="../../">あなたの名前の五格を無料で鑑定する</a>
        <p class="field-hint">完全無料・登録不要・入力内容は保存されません</p>
      </div>

      <section class="section-block">
        <h2 class="section-title">同じ「{rank}」の画数</h2>
        <div class="same-rank">{same_links}</div>
      </section>

      <div class="kazu-nav">
        <a href="../{prev_n}/">← {prev_n}画「{meanings[prev_n]['title']}」</a>
        <a href="../">一覧へ</a>
        <a href="../{next_n}/">{next_n}画「{meanings[next_n]['title']}」 →</a>
      </div>

      <p class="disclaimer">※本ページの解説はエンターテインメントを目的としたものです。数意は流派により解釈が異なる場合があります。82画以上は81を引いた数（81周期）で読みます。</p>
    </main>
    <footer class="site-footer">
      <p><a href="../../" style="color:inherit">姓名鑑定処</a> ｜ 人生これから研究所</p>
    </footer>
  </div>
{BEACON}
</body>
</html>
"""


def hub_page(meanings):
    counts = {}
    for v in meanings.values():
        counts[v["rank"]] = counts.get(v["rank"], 0) + 1
    legend = "・".join(f"{r}（{counts[r]}個）" for r in ["大吉", "吉", "半吉", "要注意", "凶"])
    cells = "".join(
        f'<a class="kazu-cell" href="{n}/"><span class="kn">{n}画</span> <span class="kr {RANK_CLASS[v["rank"]]}">{v["rank"]}</span><br><span class="kt">{v["title"]}</span></a>'
        for n, v in sorted(meanings.items())
    )
    ld = f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
{{"@type":"ListItem","position":1,"name":"姓名鑑定処","item":"{SITE}/"}},
{{"@type":"ListItem","position":2,"name":"画数の意味一覧","item":"{SITE}/kazu/"}}]}}
</script>'''
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
{HEAD_COMMON.format(css="../css/style.css?v=20260716")}
<title>画数の意味一覧【1〜81画】姓名判断の数意早見表（無料）｜姓名鑑定処</title>
<meta name="description" content="姓名判断で使う1〜81画すべての数意（画数の意味・吉凶）を一覧で解説。大吉・吉・半吉・要注意・凶の分類つき早見表。気になる画数をタップすると、五格ごとの詳しい読み方がわかります。">
<link rel="canonical" href="{SITE}/kazu/">
<meta property="og:type" content="website">
<meta property="og:title" content="画数の意味一覧【1〜81画】姓名判断の数意早見表">
<meta property="og:site_name" content="姓名鑑定処">
{ld}
</head>
<body>
  <div class="wrap">
    <header class="site-header">
      <div class="brand-seal">鑑定</div>
      <h1 class="site-title">姓名鑑定処<small>SEIMEI KANTEI-DOKORO</small></h1>
      <p class="site-sub">画数の意味（数意）一覧——1画から81画まで、名前に宿る数の物語。</p>
    </header>
    <main>
      <div class="crumb"><a href="../">姓名鑑定処</a> ／ 画数の意味一覧</div>
      <section class="section-block">
        <h2 class="section-title">画数の意味一覧【1〜81画】</h2>
        <p class="intro-lead">姓名判断では、画数それぞれに「数意（すうい）」と呼ばれる意味があるとされます。ここでは1〜81画すべての数意を一覧にしました（{legend}）。気になる画数を選ぶと、五格（天格・人格・地格・外格・総格）ごとの読み方まで詳しく確認できます。</p>
        <div class="kazu-grid">
          {cells}
        </div>
      </section>

      <div class="kazu-cta">
        <a class="btn-primary" href="../">あなたの名前の五格を無料で鑑定する</a>
        <p class="field-hint">完全無料・登録不要・入力内容は保存されません</p>
      </div>

      <p class="disclaimer">※本ページの解説はエンターテインメントを目的としたものです。数意は流派により解釈が異なる場合があります。82画以上は81を引いた数（81周期）で読みます。</p>
    </main>
    <footer class="site-footer">
      <p><a href="../" style="color:inherit">姓名鑑定処</a> ｜ 人生これから研究所</p>
    </footer>
  </div>
{BEACON}
</body>
</html>
"""


def sitemap(meanings):
    urls = [f"{SITE}/", f"{SITE}/kazu/"] + [f"{SITE}/kazu/{n}/" for n in sorted(meanings)]
    body = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>" for u in urls
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


def main():
    meanings = parse_meanings()
    assert len(meanings) == 81, f"数意が81件ではない: {len(meanings)}"
    kazu = BASE / "kazu"
    kazu.mkdir(exist_ok=True)
    (kazu / "index.html").write_text(hub_page(meanings), encoding="utf-8", newline="\n")
    for n, m in meanings.items():
        d = kazu / str(n)
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(page_for(n, m, meanings), encoding="utf-8", newline="\n")
    (BASE / "sitemap.xml").write_text(sitemap(meanings), encoding="utf-8", newline="\n")
    print(f"OK: hub + {len(meanings)} pages + sitemap.xml")


if __name__ == "__main__":
    main()
