// 我的探店之旅 — 共用互動：想去清單、照片燈箱、聯絡表單
(function () {
  var KEY = "food-want";

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; }
  }
  function save(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) { /* 無痕模式等情況就不記 */ }
  }

  // 想去：同一家店在一覽表和店家頁共用同一個勾選狀態
  var wanted = load();
  var boxes = document.querySelectorAll("input[data-want]");
  boxes.forEach(function (box) {
    var id = box.getAttribute("data-want");
    box.checked = wanted.indexOf(id) !== -1;
    box.addEventListener("change", function () {
      wanted = load().filter(function (x) { return x !== id; });
      if (box.checked) wanted.push(id);
      save(wanted);
      updateCount();
    });
  });
  function updateCount() {
    var el = document.querySelector("[data-want-count]");
    if (!el) return;
    var n = load().length;
    el.textContent = n ? "你勾了 " + n + " 家想去，下次出門前回來看看。" : "勾選「想去」，這台裝置會幫你記住。";
  }
  updateCount();

  // 照片燈箱
  var dialog = document.querySelector(".lightbox");
  if (dialog && typeof dialog.showModal === "function") {
    var big = dialog.querySelector("img");
    document.querySelectorAll("[data-zoom]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var img = btn.querySelector("img");
        if (btn.classList.contains("broken")) return;
        big.src = img.currentSrc || img.src;
        big.alt = img.alt;
        dialog.showModal();
      });
    });
    dialog.addEventListener("click", function (e) { if (e.target === dialog) dialog.close(); });
  }

  // 聯絡表單：送到 server.js 的 /submit_contact_form
  var form = document.querySelector(".contact-form form");
  if (form) {
    var status = form.querySelector(".form-status");
    var btn = form.querySelector("button[type=submit]");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      btn.disabled = true;
      btn.textContent = "送出中…";
      status.className = "form-status";
      status.textContent = "";
      fetch(form.action, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams(new FormData(form)).toString()
      }).then(function (res) {
        if (!res.ok) throw new Error(res.status);
        form.reset();
        status.className = "form-status ok";
        status.textContent = "留言已送出，謝謝你！我們會盡快回信。";
      }).catch(function () {
        status.className = "form-status err";
        status.textContent = "留言沒有送出，請稍後再試一次。";
      }).finally(function () {
        btn.disabled = false;
        btn.textContent = "送出留言";
      });
    });
  }
})();
