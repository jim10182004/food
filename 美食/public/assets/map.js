// 美食地圖頁：拖曳旋轉 3D 地面，菜牌圖釘跟著投影；「想去」和其他頁共用同一份記錄
(function () {
  var app = document.querySelector(".map-app");
  if (!app) return;
  var DATA = JSON.parse(document.getElementById("map-data").textContent);
  var SHOPS = DATA.shops, CATS = DATA.cats;
  var KEY = "food-want";
  var HOME = { rot: -14, tilt: 54, zoom: 0.76, cx: 440, cy: 560 };
  var S = { rot: HOME.rot, tilt: HOME.tilt, zoom: HOME.zoom, cx: HOME.cx, cy: HOME.cy, cat: "all", sel: -1 };
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var stage = app.querySelector(".stage");
  var anchor = app.querySelector(".anchor");
  var plane = app.querySelector(".plane");
  var overlay = app.querySelector(".overlay");
  var compass = app.querySelector(".compass svg");
  var tiltInput = app.querySelector(".tilt-ctrl input");
  var card = app.querySelector(".shop-card");
  var rowsEl = app.querySelector(".shop-rows");
  var countEl = app.querySelector("[data-count]");
  var emptyEl = app.querySelector(".shop-index-empty");
  var chipsEl = app.querySelector(".chips");

  function loadWant() { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; } }
  function saveWant(list) { try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) {} }
  function isWanted(s) { return loadWant().indexOf(s.href) !== -1; }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  var HEART = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/></svg>';

  // ---------- 圖釘與地標 ----------
  var pins = SHOPS.map(function (s, i) {
    var pin = el("div", "pin");
    pin.appendChild(el("span", "dot cat-" + s.cat));
    var body = el("div", "pin-body");
    var btn = el("button", "pin-btn");
    btn.type = "button";
    btn.setAttribute("aria-label", s.name + "，" + s.catName + "，" + s.area);
    btn.setAttribute("aria-pressed", "false");
    btn.appendChild(el("span", "tag", s.name));
    btn.appendChild(el("span", "tile cat-" + s.cat, s.glyph));
    btn.addEventListener("click", function () { select(i); });
    body.appendChild(btn);
    body.appendChild(el("span", "stick"));
    pin.appendChild(body);
    overlay.appendChild(pin);
    return { pin: pin, body: body, btn: btn };
  });
  var marks = DATA.marks.map(function (m) {
    var n = el("span", "lm", m.label);
    n.setAttribute("aria-hidden", "true");
    overlay.appendChild(n);
    return n;
  });

  // ---------- 投影（和 CSS 的 perspective:1600px 一致） ----------
  var P = 1600;
  function draw() {
    anchor.style.transform = "scale(" + S.zoom + ") rotateX(" + S.tilt + "deg) rotateZ(" + S.rot + "deg)";
    plane.style.left = -S.cx + "px";
    plane.style.top = -S.cy + "px";
    compass.style.transform = "rotate(" + S.rot + "deg)";
    tiltInput.value = Math.round(S.tilt);
    var r = S.rot * Math.PI / 180, t = S.tilt * Math.PI / 180;
    var cr = Math.cos(r), sr = Math.sin(r), ct = Math.cos(t), st = Math.sin(t);
    function proj(x, y, h) {
      var px = x - S.cx, py = y - S.cy;
      var x1 = px * cr - py * sr, y1 = px * sr + py * cr;
      var y2 = y1 * ct - h * st, zz = y1 * st + h * ct;
      var f = P / Math.max(200, P - zz);
      return { sx: S.zoom * x1 * f, sy: S.zoom * y2 * f, f: f, d: zz };
    }
    var k0 = Math.min(1.25, 0.6 + S.zoom * 0.42);
    SHOPS.forEach(function (s, i) {
      var q = proj(s.x, s.y, 0), p = pins[i];
      p.pin.style.left = "calc(50% + " + q.sx.toFixed(1) + "px)";
      p.pin.style.top = "calc(50% + " + q.sy.toFixed(1) + "px)";
      p.pin.style.zIndex = Math.round(2000 + q.d) + (S.sel === i ? 5000 : 0);
      p.body.style.transform = "translate(-50%, -100%) scale(" + (q.f * k0).toFixed(3) + ")";
    });
    DATA.marks.forEach(function (m, i) {
      var q = proj(m.x, m.y, m.h);
      marks[i].style.left = "calc(50% + " + q.sx.toFixed(1) + "px)";
      marks[i].style.top = "calc(50% + " + q.sy.toFixed(1) + "px)";
      marks[i].style.zIndex = Math.round(1000 + q.d);
    });
  }
  var queued = false;
  function redraw() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () { queued = false; draw(); });
  }

  var raf = 0;
  function animateTo(target, ms) {
    cancelAnimationFrame(raf);
    if (reduce) { for (var k in target) S[k] = target[k]; redraw(); return; }
    var dur = ms || 650, from = {}, t0 = performance.now();
    for (var key in target) from[key] = S[key];
    function step(now) {
      var u = Math.min(1, (now - t0) / dur);
      var e = u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
      for (var kk in target) S[kk] = from[kk] + (target[kk] - from[kk]) * e;
      draw();
      if (u < 1) raf = requestAnimationFrame(step);
    }
    raf = requestAnimationFrame(step);
  }

  // ---------- 篩選、清單、卡片 ----------
  function visible() {
    var want = loadWant();
    return SHOPS.filter(function (s) {
      if (S.cat === "all") return true;
      if (S.cat === "want") return want.indexOf(s.href) !== -1;
      return s.cat === S.cat;
    });
  }

  function renderChips() {
    var want = loadWant();
    var list = [{ id: "all", name: "全部", sw: "" }]
      .concat(CATS.map(function (c) { return { id: c.id, name: c.name, sw: "cat-" + c.id }; }))
      .concat([{ id: "want", name: "想去", sw: "cat-chinese" }]);
    chipsEl.innerHTML = "";
    list.forEach(function (c) {
      var n = c.id === "all" ? SHOPS.length
        : c.id === "want" ? SHOPS.filter(function (s) { return want.indexOf(s.href) !== -1; }).length
        : SHOPS.filter(function (s) { return s.cat === c.id; }).length;
      var li = el("li");
      var b = el("button", "chip");
      b.type = "button";
      b.setAttribute("aria-pressed", S.cat === c.id ? "true" : "false");
      if (c.sw) b.appendChild(el("span", "sw " + c.sw));
      b.appendChild(document.createTextNode(c.name));
      b.appendChild(el("span", "n", String(n)));
      b.addEventListener("click", function () {
        S.cat = c.id;
        if (S.sel >= 0 && visible().indexOf(SHOPS[S.sel]) === -1) S.sel = -1;
        renderAll();
      });
      li.appendChild(b);
      chipsEl.appendChild(li);
    });
  }

  function renderRows() {
    var vis = visible(), want = loadWant();
    rowsEl.innerHTML = "";
    vis.forEach(function (s) {
      var i = SHOPS.indexOf(s);
      var li = el("li");
      var b = el("button", "shop-row");
      b.type = "button";
      b.setAttribute("aria-pressed", S.sel === i ? "true" : "false");
      b.appendChild(el("span", "mini cat-" + s.cat, s.glyph));
      var txt = el("span", "txt");
      txt.appendChild(el("strong", null, s.name));
      txt.appendChild(el("span", null, s.area + "・" + s.catName));
      b.appendChild(txt);
      if (want.indexOf(s.href) !== -1) {
        var h = el("span", "heart");
        h.innerHTML = HEART;
        h.setAttribute("role", "img");
        h.setAttribute("aria-label", "已存想去");
        b.appendChild(h);
      }
      b.addEventListener("click", function () { select(i); });
      li.appendChild(b);
      rowsEl.appendChild(li);
    });
    countEl.textContent = vis.length + " 家";
    emptyEl.hidden = vis.length !== 0;
    pins.forEach(function (p, i) {
      p.pin.hidden = vis.indexOf(SHOPS[i]) === -1;
      p.btn.setAttribute("aria-pressed", S.sel === i ? "true" : "false");
    });
  }

  function fill(name, value) {
    card.querySelectorAll('[data-f="' + name + '"]').forEach(function (n) { n.textContent = value; });
  }
  function renderCard() {
    if (S.sel < 0) { card.hidden = true; return; }
    var s = SHOPS[S.sel];
    card.hidden = false;
    var mini = card.querySelector(".card-top .mini");
    mini.className = "mini cat-" + s.cat;
    mini.textContent = s.glyph;
    fill("name", s.name);
    fill("meta", s.catName + "・" + s.area);
    fill("intro", s.intro);
    fill("said", s.said ? "「" + s.said + "」" : "");
    fill("who", s.who ? "— " + s.who + "的探店筆記" : "");
    card.querySelector(".card-said").hidden = !s.said;
    fill("addr", s.addr);
    fill("hours", s.hours);
    fill("tel", s.tel);
    var fig = card.querySelector(".card-photo"), img = fig.querySelector("img");
    fig.classList.remove("broken");
    img.alt = s.name + " 的照片";
    img.src = s.cover;
    card.querySelector("[data-link]").href = s.href;
    var w = isWanted(s), wb = card.querySelector(".want-btn");
    wb.setAttribute("aria-pressed", w ? "true" : "false");
    wb.querySelector("span").textContent = w ? "已存想去" : "想去";
  }

  function renderAll() { renderChips(); renderRows(); renderCard(); redraw(); }

  function select(i) {
    if (S.sel === i) { S.sel = -1; renderAll(); return; }
    S.sel = i;
    renderAll();
    animateTo({ cx: SHOPS[i].x, cy: SHOPS[i].y, zoom: Math.max(S.zoom, 1.1) });
  }

  card.querySelector(".card-photo img").addEventListener("error", function () {
    this.parentNode.classList.add("broken");
  });
  card.querySelector("[data-close]").addEventListener("click", function () { S.sel = -1; renderAll(); });
  card.querySelector(".want-btn").addEventListener("click", function () {
    if (S.sel < 0) return;
    var id = SHOPS[S.sel].href;
    var list = loadWant().filter(function (x) { return x !== id; });
    if (!isWanted(SHOPS[S.sel])) list.push(id);
    saveWant(list);
    if (S.cat === "want" && list.indexOf(id) === -1) S.sel = -1;
    renderAll();
  });
  function stepShop(dir) {
    var vis = visible();
    if (!vis.length) return;
    var idx = vis.indexOf(SHOPS[S.sel]);
    var next = SHOPS.indexOf(vis[(idx + dir + vis.length) % vis.length]);
    if (next !== S.sel) select(next);
  }
  card.querySelector("[data-prev]").addEventListener("click", function () { stepShop(-1); });
  card.querySelector("[data-next]").addEventListener("click", function () { stepShop(1); });

  // ---------- 控制鈕 ----------
  function on(sel, fn) { app.querySelector(sel).addEventListener("click", fn); }
  on("[data-rot-l]", function () { animateTo({ rot: S.rot - 45 }); });
  on("[data-rot-r]", function () { animateTo({ rot: S.rot + 45 }); });
  on("[data-zoom-in]", function () { animateTo({ zoom: Math.min(2.2, S.zoom * 1.3) }, 350); });
  on("[data-zoom-out]", function () { animateTo({ zoom: Math.max(0.45, S.zoom / 1.3) }, 350); });
  on("[data-tour]", function () { animateTo({ rot: S.rot + 360 }, 6000); });
  on("[data-reset]", function () { S.sel = -1; renderAll(); animateTo(HOME); });
  var nightBtn = app.querySelector("[data-night]");
  nightBtn.addEventListener("click", function () {
    var night = !app.classList.contains("night");
    app.classList.toggle("night", night);
    nightBtn.setAttribute("aria-pressed", night ? "true" : "false");
    nightBtn.querySelector("span").textContent = night ? "夜景" : "白天";
  });
  tiltInput.addEventListener("input", function () { cancelAnimationFrame(raf); S.tilt = Number(tiltInput.value); redraw(); });

  // ---------- 拖曳旋轉（滑鼠、觸控都可以） ----------
  var drag = null;
  stage.addEventListener("pointerdown", function (e) {
    if (e.target.closest("button, input, label, a")) return;
    cancelAnimationFrame(raf);
    drag = { x: e.clientX, y: e.clientY, rot: S.rot, tilt: S.tilt, id: e.pointerId };
    stage.setPointerCapture(e.pointerId);
    stage.classList.add("dragging");
  });
  stage.addEventListener("pointermove", function (e) {
    if (!drag || e.pointerId !== drag.id) return;
    S.rot = drag.rot + (e.clientX - drag.x) * 0.35;
    S.tilt = Math.max(20, Math.min(72, drag.tilt - (e.clientY - drag.y) * 0.25));
    redraw();
  });
  function end() { drag = null; stage.classList.remove("dragging"); }
  stage.addEventListener("pointerup", end);
  stage.addEventListener("pointercancel", end);

  // 網址帶 #店家頁 就直接選那家，例如 map.html#ramen1
  var hash = location.hash.slice(1);
  var start = SHOPS.findIndex(function (s) { return s.href === hash + ".html"; });
  renderAll();
  if (start >= 0) select(start);
})();
