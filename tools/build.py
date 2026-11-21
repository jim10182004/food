"""讀 tools/content.json，產生 美食/public/ 底下所有頁面。

用法：python tools/build.py
改店家文字或照片 → 改 content.json，再跑一次這支程式。
"""
import json, re
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
PUB = ROOT.parent / "美食" / "public"
DATA = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))

# 舊版有些標題寫錯（咖啡館頁標成「夜市」），這裡統一
CAT_META = {
    "chinese_restaurant": ("中式餐廳", "中式", "蝦仁飯、酸菜魚、手工水餃，吃得飽又不貴的中式味道。"),
    "foreign_restaurant": ("西式餐廳", "西式", "從平價小漢堡到景觀餐廳，想吃漢堡和美式料理就看這裡。"),
    "bistro":             ("餐酒館", "餐酒館", "下課下班後想喝一杯，餐點也要好吃的地方。"),
    "ramen":              ("拉麵館", "拉麵", "清爽系到濃郁系，三碗口味差很多的拉麵。"),
    "cafes":              ("咖啡館", "咖啡館", "咖啡、甜點，還有可以坐久一點的店。"),
    "night_market":       ("夜市", "夜市", "士林夜市一帶的蚵仔煎、平價牛排和炸熱狗。"),
}
YEAR = "2024–2026"
FONTS = ("https://fonts.googleapis.com/css2?family=LXGW+WenKai+TC:wght@400;700"
         "&family=Noto+Sans+TC:wght@400;500;700&display=swap")

e = lambda s: escape(s or "", quote=True)


def shop_name(s):
    return re.sub(r"^《|》$", "", s["name"]).strip()


def area(addr):
    m = re.search(r"(?:市|縣)(\S{1,3}?區)", addr or "")
    return m.group(1) if m else ""


def split_review(text):
    m = re.match(r"\s*([^:：\s]{1,4})\s*[:：]\s*(.*)", text or "", re.S)
    return (m.group(1), m.group(2).strip()) if m else ("", (text or "").strip())


def photo(src, alt, label, cls="ph", tag="div", extra=""):
    return (f'<{tag} class="{cls}"{extra}>'
            f'<img src="{e(src)}" alt="{e(alt)}" loading="lazy" referrerpolicy="no-referrer" '
            f'onerror="this.parentNode.classList.add(\'broken\')">'
            f'<span class="ph-fallback" aria-hidden="true">{e(label)}<br>照片暫時載不到</span>'
            f'</{tag}>')


def photo_credit(s):
    """照片出處：有記錄來源文章就連過去，否則列出照片所在網站。"""
    from urllib.parse import urlparse
    if s.get("photo_source"):
        host = urlparse(s["photo_source"]).netloc.removeprefix("www.")
        return f'照片出處：<a href="{e(s["photo_source"])}" target="_blank" rel="noopener">{e(host)}</a>'
    hosts = []
    for u in [s["cover"], *s["gallery"]]:
        p = urlparse(u)
        h = p.netloc
        if h.startswith("i0.wp.com") or h.startswith("i1.wp.com"):
            h = p.path.strip("/").split("/")[0]
        h = re.sub(r"^(www|live|i|pgw)\.", "", h)
        h = re.sub(r"^\d\.bp\.", "", h)
        h = {"staticflickr.com": "flickr.com", "udn.com.tw": "udn.com"}.get(h, h)
        if h not in hosts:
            hosts.append(h)
    return "照片出處：" + "、".join(e(h) for h in hosts)


def want_box(shop_id, label):
    return (f'<label class="want"><input type="checkbox" data-want="{e(shop_id)}" '
            f'aria-label="{e(label)}"><span class="box" aria-hidden="true"></span></label>')


def page(title, body, current="", desc="小羊和微笑的台北探店筆記：中式、西式、餐酒館、拉麵、咖啡館和夜市。",
         extra_css="", extra_js=""):
    nav = []
    for c in DATA:
        name = CAT_META[c["slug"]][0]
        cur = ' aria-current="page"' if current == c["slug"] else ""
        nav.append(f'<li><a href="{c["slug"]}.html"{cur}>{name}</a></li>')
    cur = ' aria-current="page"' if current == "map" else ""
    nav.append(f'<li><a href="map.html"{cur}>美食地圖</a></li>')
    cur = ' aria-current="page"' if current == "contact" else ""
    nav.append(f'<li class="nav-contact"><a href="contact.html"{cur}>聯絡我們</a></li>')
    return f"""<!DOCTYPE html>
<html lang="zh-Hant-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="assets/site.css">{extra_css}
</head>
<body>
<a class="skip" href="#main">跳到主要內容</a>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="index.html">我的探店之旅</a>
    <nav class="site-nav" aria-label="網站導覽"><ul>{''.join(nav)}</ul></nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <p>&copy; {YEAR} 我的探店之旅　點評：小羊、微笑</p>
    <p>店家資料整理於 2024 年，營業時間可能變動，出發前請先確認。</p>
  </div>
</footer>
<script src="assets/site.js"></script>{extra_js}
</body>
</html>
"""


def write(name, html):
    (PUB / name).write_text(html, encoding="utf-8", newline="\n")


# ---------- 首頁 ----------
total = sum(len(c["shops"]) for c in DATA)
plaques = "".join(
    f'<li><a class="plaque" href="{c["slug"]}.html">'
    f'<span class="plaque-name">{CAT_META[c["slug"]][1]}</span>'
    f'<span class="plaque-count"><span class="tcy">{len(c["shops"])}</span>家</span></a></li>'
    for c in DATA)

rows = []
for c in DATA:
    cname = CAT_META[c["slug"]][0]
    for s in c["shops"]:
        n = shop_name(s)
        who, _ = split_review(s["reviews"][0] if s["reviews"] else "")
        a = area(s["info"].get("地址"))
        rows.append(
            f'<tr><td class="col-want">{want_box(s["href"], "想去 " + n)}</td>'
            f'<td><a href="{s["href"]}">{e(n)}</a>'
            f'<span class="row-meta">{cname}　{e(a)}</span></td>'
            f'<td class="col-cat"><a href="{c["slug"]}.html" class="muted">{cname}</a></td>'
            f'<td class="col-area muted">{e(a)}</td>'
            f'<td class="col-who muted">{e(who)}</td></tr>')

home = f"""<div class="wrap">
  <section class="hero" aria-labelledby="hero-title">
    <div>
      <h1 id="hero-title">台北這幾家，<br>我們吃過才寫。</h1>
      <p>小羊和微笑的探店筆記：6 種類別、{total} 家店，每家都附上地址、電話、營業時間，還有我們自己的真心話。</p>
    </div>
    <div>
      <p class="hero-prompt">今天想吃什麼？</p>
      <nav class="plaque-wall" aria-label="店家類別"><ul class="plaques">{plaques}</ul></nav>
    </div>
  </section>

  <section class="map-teaser" aria-labelledby="teaser-title">
    <div>
      <h2 id="teaser-title">把 {total} 家店放到台北地圖上</h2>
      <p>可以拖曳旋轉的 3D 地圖，點菜牌就看得到店家、順便存進想去清單。</p>
    </div>
    <a class="btn" href="map.html">打開美食地圖</a>
  </section>

  <section aria-labelledby="list-title">
    <div class="section-head">
      <h2 id="list-title">{total} 家店一覽</h2>
      <p data-want-count>勾選「想去」，這台裝置會幫你記住。</p>
    </div>
    <div class="order-sheet">
      <table>
        <thead><tr><th class="col-want" scope="col">想去</th><th scope="col">店名</th>
        <th class="col-cat" scope="col">類別</th><th class="col-area" scope="col">地區</th>
        <th class="col-who" scope="col">寫的人</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </section>
</div>"""
write("index.html", page("我的探店之旅｜小羊和微笑的台北探店筆記", home))

# ---------- 類別頁與店家頁 ----------
for c in DATA:
    slug = c["slug"]
    cname, _, lede = CAT_META[slug]
    items = []
    for s in c["shops"]:
        n = shop_name(s)
        who, rev = split_review(s["reviews"][0] if s["reviews"] else "")
        a = area(s["info"].get("地址"))
        items.append(f"""<li class="shop-item">
      {photo(s["cover"], n + " 的照片", n, tag="a", extra=f' href="{s["href"]}" tabindex="-1" aria-hidden="true"')}
      <div>
        <h2><a href="{s["href"]}">{e(n)}</a></h2>
        <p class="shop-area">{e(a)}</p>
        <p class="shop-intro">{e(s["intro"])}</p>
        {f'<p class="note"><span class="who">{e(who)}</span>{e(rev)}</p>' if rev else ''}
        <a class="shop-more" href="{s["href"]}">看完整介紹和地址</a>
      </div>
    </li>""")
    body = f"""<div class="wrap">
  <header class="page-head">
    <p class="crumb"><a href="index.html">首頁</a></p>
    <h1>{cname}</h1>
    <p class="lede">{lede}</p>
  </header>
  <ul class="shop-list">
    {''.join(items)}
  </ul>
</div>"""
    write(f"{slug}.html", page(f"{cname}｜我的探店之旅", body, current=slug, desc=lede))

    shops = c["shops"]
    for i, s in enumerate(shops):
        n = shop_name(s)
        who, rev = split_review(s["reviews"][0] if s["reviews"] else "")
        info = s["info"]
        addr, tel, hours = info.get("地址", ""), info.get("電話", ""), info.get("營業時間", "")
        gallery = "".join(
            photo(src, f"{n} 照片 {k + 1}", n, tag="button",
                  extra=f' type="button" data-zoom aria-label="放大 {e(n)} 照片 {k + 1}"')
            for k, src in enumerate(s["gallery"][:3]))
        map_url = "https://www.google.com/maps/search/?api=1&query=" + quote(addr)
        tel_digits = re.sub(r"[^\d+]", "", tel)
        prev_s = shops[i - 1] if i > 0 else None
        next_s = shops[i + 1] if i + 1 < len(shops) else None
        pager = ""
        if prev_s:
            pager += f'<a class="prev" href="{prev_s["href"]}"><span>上一家</span><strong>{e(shop_name(prev_s))}</strong></a>'
        if next_s:
            pager += f'<a class="next" href="{next_s["href"]}"><span>下一家</span><strong>{e(shop_name(next_s))}</strong></a>'
        if not next_s:
            pager += f'<a class="next" href="{slug}.html"><span>看完了</span><strong>回到{cname}</strong></a>'

        body = f"""<div class="wrap">
  <header class="page-head">
    <p class="crumb"><a href="{slug}.html">{cname}</a></p>
    <h1>{e(n)}</h1>
    <p class="lede">{e(area(addr))}</p>
  </header>
  <div class="gallery gallery-{len(s["gallery"][:3])}">{gallery}</div>
  <p class="credit">{photo_credit(s)}</p>
  <div class="shop-body">
    <div>
      {f'<section class="about"><h2>{e(who)}的點評</h2><p class="note">{e(rev)}</p></section>' if rev else ''}
      <section class="about"><h2>店家介紹</h2><p>{e(s["intro"])}</p></section>
    </div>
    <aside class="slip" aria-labelledby="slip-title">
      <h2 id="slip-title">店家資訊</h2>
      <dl>
        <div class="row"><dt>地址</dt><dd>{e(addr)}<br><a href="{map_url}" target="_blank" rel="noopener">在 Google 地圖開啟</a>　<a href="map.html#{s["href"].removesuffix(".html")}">在美食地圖上看</a></dd></div>
        <div class="row"><dt>電話</dt><dd>{f'<a class="tel" href="tel:{tel_digits}">{e(tel)}</a>' if tel_digits else e(tel)}</dd></div>
        <div class="row"><dt>營業時間</dt><dd>{e(hours)}</dd></div>
      </dl>
      <div class="slip-foot">
        <label class="want-label">{want_box(s["href"], "想去 " + n)}想去這家</label>
        <p>資料整理於 2024 年，出發前請先確認營業時間。</p>
      </div>
    </aside>
  </div>
  <nav class="pager" aria-label="同類別的其他店">{pager}</nav>
</div>
<dialog class="lightbox" aria-label="放大照片">
  <form method="dialog"><button>關閉</button></form>
  <img alt="">
</dialog>"""
        desc = f"{n}（{cname}，{area(addr)}）：地址、電話、營業時間和版主點評。"
        write(s["href"], page(f"{n}｜{cname}｜我的探店之旅", body, current=slug, desc=desc))

# ---------- 美食地圖頁 ----------
# 座標是依地址估算、畫在 860×1110 的示意地面上（content.json 每家店的 map.x / map.y）
MAP_CAT = {  # slug → (圖釘 CSS 類別, 菜牌字)
    "chinese_restaurant": ("chinese", "中"), "foreign_restaurant": ("western", "西"),
    "bistro": ("bistro", "酒"), "ramen": ("ramen", "麵"), "cafes": ("cafe", "咖"),
    "night_market": ("night", "夜"),
}
DISTRICTS = [("士林區", 420, 50), ("內湖區", 760, 190), ("中山區", 420, 480), ("松山區", 640, 500),
             ("大同區", 190, 530), ("萬華區", 170, 860), ("中正區", 320, 870), ("大安區", 560, 1000),
             ("信義區", 780, 640), ("文山區", 620, 1080)]
# 山丘：(left, top, w, h, 顏色層, 高度)
HILLS = [(540, 5, 300, 130, 1, 6), (575, 20, 230, 100, 2, 18), (610, 35, 160, 70, 3, 32), (645, 50, 90, 40, 4, 46),
         (785, 820, 70, 120, 1, 6), (795, 837, 50, 86, 2, 16), (805, 854, 30, 52, 3, 26),
         (630, 1020, 180, 80, 1, 6), (660, 1033, 120, 54, 2, 16), (690, 1046, 60, 28, 3, 26)]
# 房子：(left, top, w, h, 高, 類別)；st = 台北車站、tw = 101
BLOCKS = [(204, 622, 36, 22, 14, "st"), (688, 773, 30, 30, 22, "tw"), (692, 777, 22, 22, 120, "tw"), (701, 786, 4, 4, 150, ""),
          (150, 560, 24, 24, 34, ""), (258, 618, 22, 30, 46, ""), (322, 650, 26, 22, 30, ""), (350, 560, 30, 24, 56, ""),
          (420, 600, 24, 24, 40, ""), (540, 612, 26, 26, 62, ""), (598, 556, 30, 22, 36, ""), (662, 600, 22, 22, 48, ""),
          (762, 690, 26, 30, 72, ""), (650, 700, 24, 24, 52, ""), (762, 742, 22, 26, 86, ""), (742, 806, 24, 22, 58, ""),
          (500, 722, 28, 24, 34, ""), (520, 800, 24, 30, 44, ""), (430, 760, 26, 22, 28, ""), (360, 780, 22, 24, 38, ""),
          (200, 760, 24, 26, 26, ""), (160, 720, 22, 22, 32, ""), (470, 940, 26, 24, 30, ""), (360, 940, 24, 22, 24, ""),
          (560, 440, 30, 26, 42, ""), (690, 430, 26, 24, 36, ""), (330, 420, 22, 22, 30, ""), (240, 470, 24, 22, 28, ""),
          (390, 200, 24, 26, 26, ""), (210, 120, 22, 24, 22, ""), (690, 250, 30, 26, 50, ""), (780, 236, 24, 22, 40, "")]
MARKS = [{"label": "台北101", "x": 703, "y": 788, "h": 160}, {"label": "台北車站", "x": 222, "y": 633, "h": 22},
         {"label": "士林夜市", "x": 318, "y": 236, "h": 0}, {"label": "陽明山", "x": 690, "y": 70, "h": 56}]

map_shops = []
for c in DATA:
    cls, glyph = MAP_CAT[c["slug"]]
    for s in c["shops"]:
        who, rev = split_review(s["reviews"][0] if s["reviews"] else "")
        info = s["info"]
        map_shops.append({
            "name": shop_name(s), "cat": cls, "glyph": glyph, "catName": CAT_META[c["slug"]][0],
            "area": area(info.get("地址")), "x": s["map"]["x"], "y": s["map"]["y"],
            "intro": s["intro"], "who": who, "said": rev, "addr": info.get("地址", ""),
            "hours": info.get("營業時間", ""), "tel": info.get("電話", ""),
            "href": s["href"], "cover": s["cover"]})
map_json = json.dumps({"shops": map_shops, "marks": MARKS,
                       "cats": [{"id": MAP_CAT[c["slug"]][0], "name": CAT_META[c["slug"]][0]} for c in DATA]},
                      ensure_ascii=False).replace("</", "<\\/")

faces = '<i class="t"></i><i class="n"></i><i class="s"></i><i class="w"></i><i class="e"></i>'
plane = "".join(f'<div class="district" style="left:{x}px;top:{y}px">{n}</div>' for n, x, y in DISTRICTS)
plane += "".join(f'<div class="mt" style="left:{l}px;top:{t}px;width:{w}px;height:{h}px;'
                 f'background:var(--mt{k});transform:translateZ({z}px)"></div>' for l, t, w, h, k, z in HILLS)
plane += "".join(f'<div class="bx{" " + k if k else ""}" style="left:{l}px;top:{t}px;width:{w}px;height:{h}px;--h:{z}px">{faces}</div>'
                 for l, t, w, h, z, k in BLOCKS)
legend = "".join(f'<li><span class="mini cat-{MAP_CAT[c["slug"]][0]}" aria-hidden="true">{MAP_CAT[c["slug"]][1]}</span>'
                 f'{CAT_META[c["slug"]][1]}</li>' for c in DATA)

ICON = lambda d, sw="2.4": (f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>')

map_body = f"""<div class="map-app">
<div class="wrap map-wrap">
  <header class="page-head map-head">
    <p class="crumb"><a href="index.html">首頁</a></p>
    <h1>台北美食 3D 地圖</h1>
    <p class="lede">拖曳地圖轉一圈台北，點菜牌看店家。{total} 家去過的店分成 6 類，想去的先存起來。</p>
  </header>
  <div class="map-layout">
    <section class="map-side" aria-label="篩選與店家">
      <ul class="chips" aria-label="依類別篩選"></ul>
      <article class="shop-card" hidden aria-live="polite">
        <div class="card-top">
          <span class="mini" aria-hidden="true" style="width:44px;height:50px;font-size:26px"></span>
          <div>
            <h2 data-f="name"></h2>
            <p class="card-meta" data-f="meta"></p>
          </div>
          <button type="button" class="mbtn icon" data-close aria-label="關閉店家資訊">{ICON('<path d="M6 6l12 12M18 6L6 18"/>')}</button>
        </div>
        <figure class="card-photo"><img alt="" referrerpolicy="no-referrer"></figure>
        <p data-f="intro"></p>
        <figure class="card-said">
          <blockquote data-f="said"></blockquote>
          <figcaption data-f="who"></figcaption>
        </figure>
        <dl class="card-info">
          <dt>地址</dt><dd data-f="addr"></dd>
          <dt>營業時間</dt><dd data-f="hours"></dd>
          <dt>電話</dt><dd data-f="tel"></dd>
        </dl>
        <div class="card-actions">
          <a class="mbtn primary" data-link href="index.html">看完整介紹</a>
          <button type="button" class="mbtn want-btn" aria-pressed="false">{ICON('<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>', "2")}<span>想去</span></button>
          <button type="button" class="mbtn" data-prev>{ICON('<path d="M15 6l-6 6 6 6"/>')}上一家</button>
          <button type="button" class="mbtn" data-next>下一家{ICON('<path d="M9 6l6 6-6 6"/>')}</button>
        </div>
        <p class="card-note">地圖位置依地址估算；資料整理於 2024 年，營業時間以店家公告為準。</p>
      </article>
      <div class="shop-index">
        <div class="shop-index-head"><h2 style="margin:0;font-size:inherit">店家一覽</h2><span data-count></span></div>
        <p class="shop-index-empty" hidden>還沒有想去的店。點開店家，按「想去」就會收進這裡。</p>
        <ul class="shop-rows"></ul>
      </div>
    </section>
    <section class="map-main" aria-label="台北立體地圖">
      <div class="stage">
        <div class="anchor">
          <div class="plane">
            <div class="side" style="left:0;top:0;width:860px;height:34px;transform-origin:0 0;transform:rotateX(-90deg)"></div>
            <div class="side b" style="left:0;top:1110px;width:860px;height:34px;transform-origin:0 0;transform:rotateX(-90deg)"></div>
            <div class="side" style="left:0;top:0;width:34px;height:1110px;transform-origin:0 0;transform:rotateY(90deg)"></div>
            <div class="side" style="left:826px;top:0;width:34px;height:1110px;transform-origin:100% 0;transform:rotateY(-90deg)"></div>
            <svg width="860" height="1110" viewBox="0 0 860 1110" aria-hidden="true">
              <g fill="none" stroke="var(--river)" stroke-linecap="round" stroke-linejoin="round">
                <path d="M40 1010 C70 900 100 820 105 760 C110 650 130 560 130 500 C125 400 80 320 30 240 L0 205" stroke-width="34"/>
                <path d="M470 1110 C400 1060 300 1020 150 978 L55 948" stroke-width="26"/>
                <path d="M860 385 C760 300 650 360 560 300 C480 250 420 330 330 362 C262 384 220 300 170 230 C140 190 110 176 40 186" stroke-width="22"/>
              </g>
              <g font-family="LXGW WenKai TC, serif" font-size="18" fill="var(--river-text)" font-weight="700">
                <text x="58" y="440" transform="rotate(-78 58 440)">淡水河</text>
                <text x="250" y="1040" transform="rotate(18 250 1040)">新店溪</text>
                <text x="600" y="340">基隆河</text>
              </g>
            </svg>
            {plane}
          </div>
        </div>
        <div class="overlay"></div>
        <div class="compass" aria-hidden="true">
          <svg width="40" height="40" viewBox="0 0 40 40"><path d="M20 4l6 16h-12z" fill="#C62230"/><path d="M20 36l-6-16h12z" fill="var(--m-line)"/><text x="20" y="14.5" text-anchor="middle" font-size="9" font-weight="700" fill="#FFFFFF">N</text></svg>
        </div>
        <div class="stage-ctrls">
          <div>
            <button type="button" class="ctrl" data-night aria-pressed="false" aria-label="夜景模式">{ICON('<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>', "2.2")}<span>白天</span></button>
            <button type="button" class="ctrl" data-rot-l aria-label="向左旋轉">{ICON('<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/>', "2.2")}</button>
            <button type="button" class="ctrl" data-rot-r aria-label="向右旋轉">{ICON('<path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 4v5h-5"/>', "2.2")}</button>
            <button type="button" class="ctrl" data-zoom-in aria-label="放大">{ICON('<path d="M12 5v14M5 12h14"/>')}</button>
            <button type="button" class="ctrl" data-zoom-out aria-label="縮小">{ICON('<path d="M5 12h14"/>')}</button>
          </div>
          <div>
            <label class="tilt-ctrl">傾斜<input type="range" min="20" max="72" step="1" value="54"></label>
            <button type="button" class="ctrl" data-tour>環繞一圈</button>
            <button type="button" class="ctrl" data-reset>重設</button>
          </div>
        </div>
      </div>
      <ul class="map-legend">{legend}<li>拖曳旋轉・位置為示意</li></ul>
    </section>
  </div>
</div>
</div>
<script type="application/json" id="map-data">{map_json}</script>"""
write("map.html", page("台北美食 3D 地圖｜我的探店之旅", map_body, current="map",
                       desc=f"把 {total} 家去過的台北餐廳放到可以旋轉的 3D 地圖上，依類別篩選、存想去清單。",
                       extra_css='\n<link rel="stylesheet" href="assets/map.css">',
                       extra_js='\n<script src="assets/map.js"></script>'))

# ---------- 聯絡頁 ----------
contact = """<div class="wrap">
  <header class="page-head">
    <p class="crumb"><a href="index.html">首頁</a></p>
    <h1>聯絡我們</h1>
    <p class="lede">想推薦店家、發現資料過期，或只是想打聲招呼，都可以留言給我們。</p>
  </header>
  <div class="contact">
    <div>
      <p class="note">有你私心推薦、我們還沒去過的店嗎？寫下店名和地區，我們排進下次的探店清單。</p>
    </div>
    <div class="contact-form">
      <form action="https://food-contact.jim20041018.workers.dev/submit_contact_form" method="post">
        <div class="field"><label for="name">你的名字</label><input type="text" id="name" name="name" autocomplete="name" maxlength="50" required></div>
        <div class="field"><label for="email">Email（回信用）</label><input type="email" id="email" name="email" autocomplete="email" maxlength="254" required></div>
        <div class="field"><label for="message">想說的話</label><textarea id="message" name="message" rows="6" maxlength="2000" required></textarea></div>
        <div class="hp" aria-hidden="true"><label for="website">網站（請留空）</label><input type="text" id="website" name="website" tabindex="-1" autocomplete="off"></div>
        <button class="btn" type="submit">送出留言</button>
        <p class="form-status" role="status" aria-live="polite"></p>
      </form>
    </div>
  </div>
</div>"""
write("contact.html", page("聯絡我們｜我的探店之旅", contact, current="contact"))

print("已產生", len(list(PUB.glob("*.html"))), "個頁面")
