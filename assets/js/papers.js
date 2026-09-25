// Research page: topic filter + search, shareable via the URL hash, and BibTeX copy buttons.
(function () {
  var filters = document.querySelector(".filters");
  if (!filters) return;
  filters.hidden = false;

  var search = filters.querySelector(".search");
  var barChips = Array.prototype.slice.call(filters.querySelectorAll(".chip"));
  var papers = Array.prototype.slice.call(document.querySelectorAll(".paper-section .paper"));
  var sections = Array.prototype.slice.call(document.querySelectorAll(".paper-section:not(.software)"));
  var statusText = filters.querySelector(".status-text");
  var clearBtn = filters.querySelector(".clear");
  var active = new Set();

  function readHash() {
    var m = /(?:^|&)topics=([^&]*)/.exec(location.hash.slice(1));
    var q = /(?:^|&)q=([^&]*)/.exec(location.hash.slice(1));
    active = new Set(m && m[1] ? decodeURIComponent(m[1]).split(",") : []);
    search.value = q ? decodeURIComponent(q[1]) : "";
  }

  function writeHash() {
    var parts = [];
    if (active.size) parts.push("topics=" + encodeURIComponent(Array.from(active).join(",")));
    if (search.value.trim()) parts.push("q=" + encodeURIComponent(search.value.trim()));
    var h = parts.length ? "#" + parts.join("&") : location.pathname + location.search;
    history.replaceState(null, "", h);
  }

  function apply() {
    var terms = search.value.toLowerCase().split(/\s+/).filter(Boolean);
    var shown = 0;
    papers.forEach(function (p) {
      var topics = (p.getAttribute("data-topics") || "").split(" ");
      var text = p.getAttribute("data-search") || "";
      var okTopic = !active.size || topics.some(function (t) { return active.has(t); });
      var okText = terms.every(function (t) { return text.indexOf(t) !== -1; });
      p.hidden = !(okTopic && okText);
      if (!p.hidden) shown++;
    });
    // hide year labels with nothing under them, and empty sections
    sections.forEach(function (s) {
      var any = false;
      var labels = s.querySelectorAll(".year-label");
      Array.prototype.forEach.call(labels, function (label) {
        var el = label.nextElementSibling, has = false;
        while (el && !el.classList.contains("year-label")) {
          if (!el.hidden) has = true;
          el = el.nextElementSibling;
        }
        label.hidden = !has;
      });
      var n = 0;
      Array.prototype.forEach.call(s.querySelectorAll(".paper"), function (p) { if (!p.hidden) n++; });
      any = n > 0;
      s.hidden = !any;
      var count = s.querySelector(".section-count");
      if (count) count.textContent = n;
    });
    document.querySelectorAll("[data-topic]").forEach(function (c) {
      var on = active.has(c.getAttribute("data-topic"));
      if (c.hasAttribute("aria-pressed")) c.setAttribute("aria-pressed", on ? "true" : "false");
      c.classList.toggle("is-on", on);
    });
    var filtering = active.size || terms.length;
    statusText.textContent = filtering ? "Showing " + shown + " of " + papers.length + " papers." : "";
    clearBtn.hidden = !filtering;
  }

  function toggle(topic) {
    if (active.has(topic)) active.delete(topic); else active.add(topic);
    writeHash();
    apply();
  }

  barChips.forEach(function (c) {
    c.addEventListener("click", function () { toggle(c.getAttribute("data-topic")); });
  });
  // Topic chips on individual papers filter to that topic and jump to the filter bar.
  document.querySelectorAll(".paper .topic-link[data-topic]").forEach(function (c) {
    c.addEventListener("click", function () {
      active = new Set([c.getAttribute("data-topic")]);
      writeHash();
      apply();
      filters.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  search.addEventListener("input", function () { writeHash(); apply(); });
  clearBtn.addEventListener("click", function () {
    active.clear();
    search.value = "";
    writeHash();
    apply();
  });
  window.addEventListener("hashchange", function () { readHash(); apply(); });

  // Abstract / BibTeX toggles (hidden until JS runs, so no-JS visitors just see links)
  document.querySelectorAll(".pill--toggle").forEach(function (btn) {
    var panel = document.getElementById(btn.getAttribute("aria-controls"));
    if (!panel) return;
    btn.hidden = false;
    btn.addEventListener("click", function () {
      var open = btn.getAttribute("aria-expanded") !== "true";
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      panel.hidden = !open;
    });
  });

  // BibTeX copy buttons
  document.querySelectorAll(".bibtex-box .copy").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.parentNode.querySelector("code").textContent;
      var done = function () {
        btn.textContent = "Copied";
        setTimeout(function () { btn.textContent = "Copy"; }, 1500);
      };
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(done, function () {});
      } else {
        var ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); done(); } catch (e) {}
        document.body.removeChild(ta);
      }
    });
  });

  readHash();
  apply();
})();
