"""從舊版 html 抽出所有店家內容，存成 content.json（只需執行一次）。"""
import json, re, sys
from pathlib import Path
from bs4 import BeautifulSoup

PUB = Path(__file__).resolve().parent.parent / "美食" / "public"
CATS = ["chinese_restaurant", "foreign_restaurant", "bistro", "ramen", "cafes", "night_market"]
clean = lambda s: re.sub(r"\s+", " ", s or "").strip()

def soup(name):
    return BeautifulSoup((PUB / name).read_text(encoding="utf-8"), "html.parser")

out = []
for c in CATS:
    s = soup(f"{c}.html")
    title = clean(s.header.h1.get_text()) if s.header and s.header.h1 else c
    shops = []
    for a in s.select("a.restaurant, .restaurant"):
        href = a.get("href") or (a.find("a") or {}).get("href")
        img = a.find("img")
        h3 = a.find("h3")
        p = a.select_one(".restaurant-info p") or a.find("p")
        shops.append({"href": href, "cover": img["src"] if img else None,
                      "name": clean(h3.get_text()) if h3 else "", "intro": clean(p.get_text()) if p else ""})
    for sh in shops:
        d = soup(sh["href"])
        box = d.select_one(".container") or d.body
        sh["gallery"] = [i["src"] for i in box.select(".gallery img")] or [i["src"] for i in box.find_all("img")]
        info = {}
        for p in box.select(".restaurant-info p"):
            t = clean(p.get_text())
            if ":" in t or "：" in t:
                k, v = re.split(r"[:：]", t, 1)
                info[clean(k)] = clean(v)
        sh["info"] = info
        sh["reviews"] = [clean(r.get_text()) for r in box.select(".review")]
        h1 = box.find("h1")
        sh["detail_title"] = clean(h1.get_text()) if h1 else ""
    out.append({"slug": c, "title": title, "shops": shops})

(Path(__file__).parent / "content.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for c in out:
    print(c["slug"], c["title"], len(c["shops"]))
    for sh in c["shops"]:
        print("  ", sh["href"], sh["name"], "| imgs", len(sh["gallery"]), "| info", list(sh["info"]), "| rev", len(sh["reviews"]), "| intro", len(sh["intro"]))
