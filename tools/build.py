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


def page(title, body, current="", desc="小羊和微笑的台北探店筆記：中式、西式、餐酒館、拉麵、咖啡館和夜市。"):
    nav = []
    for c in DATA:
        name = CAT_META[c["slug"]][0]
        cur = ' aria-current="page"' if current == c["slug"] else ""
        nav.append(f'<li><a href="{c["slug"]}.html"{cur}>{name}</a></li>')
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
<link rel="stylesheet" href="assets/site.css">
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
<script src="assets/site.js"></script>
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
        <div class="row"><dt>地址</dt><dd>{e(addr)}<br><a href="{map_url}" target="_blank" rel="noopener">在 Google 地圖開啟</a></dd></div>
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
      <form action="/submit_contact_form" method="post">
        <div class="field"><label for="name">你的名字</label><input type="text" id="name" name="name" autocomplete="name" required></div>
        <div class="field"><label for="email">Email（回信用）</label><input type="email" id="email" name="email" autocomplete="email" required></div>
        <div class="field"><label for="message">想說的話</label><textarea id="message" name="message" rows="6" required></textarea></div>
        <button class="btn" type="submit">送出留言</button>
        <p class="form-status" role="status" aria-live="polite"></p>
      </form>
    </div>
  </div>
</div>"""
write("contact.html", page("聯絡我們｜我的探店之旅", contact, current="contact"))

print("已產生", len(list(PUB.glob("*.html"))), "個頁面")
