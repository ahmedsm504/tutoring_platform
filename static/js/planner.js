/* حاسبة ختم القرآن وخطة الحفظ — نفس منطق learning/planner.py (مصحف المدينة 604 صفحة) */
(function () {
  'use strict';
  var el = document.getElementById('planner-cfg');
  if (!el) return;
  var cfg = JSON.parse(el.textContent);
  var D = cfg.data, EN = cfg.lang === 'en', TOTAL = 604;
  var $ = function (id) { return document.getElementById(id); };
  var tbody = document.querySelector('#pl-table tbody');

  function store(k, v) { try { if (v === undefined) return JSON.parse(localStorage.getItem(k) || 'null'); localStorage.setItem(k, JSON.stringify(v)); } catch (e) { return null; } }
  function num(x) { return (Math.abs(x - Math.round(x)) < 0.15 && x >= 1) ? String(Math.round(x)) : x.toFixed(1); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function juzOf(p) { var j = 1; for (var i = 0; i < 30; i++) if (D.juz[i] <= p) j = i + 1; return j; }
  function pageEnd(p) {
    if (p >= TOTAL) return [114, 6];
    var s = D.pages[p][0], a = D.pages[p][1];
    return a > 1 ? [s, a - 1] : [s - 1, D.counts[s - 2]];
  }
  function ref(sa) { return D.names[sa[0] - 1] + ' ' + sa[1]; }

  /* ------------------------------------------------ الختمة */
  function prevAyah(sa) { return sa[1] > 1 ? [sa[0], sa[1] - 1] : [sa[0] - 1, D.counts[sa[0] - 2]]; }
  function juzRows(days, kh) {
    var per = 30 * kh / days, rows = [];
    for (var d = 0; d < days; d++) {
      var ja = (d * per) % 30 + 1, jb = ((d + 1) * per - 1) % 30 + 1, p1 = D.juz[ja - 1], p2, to;
      if (jb < 30) {
        var nxt = D.jf[jb], ps = D.pages[D.juz[jb] - 1];
        p2 = (ps[0] !== nxt[0] || ps[1] !== nxt[1]) ? D.juz[jb] : D.juz[jb] - 1;
        to = prevAyah(nxt);
      } else { p2 = TOTAL; to = [114, 6]; }
      rows.push({ day: d + 1, d0: d + 1, p1: p1, p2: p2, n: p2 - p1 + 1, from: D.jf[ja - 1], to: to, j1: ja, j2: jb, kh: jb === 30 });
    }
    return rows;
  }
  function khatmaRows(days, kh, start) {
    if (start === 1 && days <= 30 * kh && (30 * kh) % days === 0) return { rows: juzRows(days, kh), weekly: false };
    var total = TOTAL * kh, rows = [];
    for (var d = 0; d < days; d++) {
      var a = Math.round(d * total / days), b = Math.round((d + 1) * total / days);
      if (b <= a) continue;
      var p1 = (start - 1 + a) % TOTAL + 1, p2 = (start - 1 + b - 1) % TOTAL + 1;
      rows.push({ day: d + 1, p1: p1, p2: p2, n: b - a, from: D.pages[p1 - 1], to: pageEnd(p2), j1: juzOf(p1), j2: juzOf(p2), kh: b % TOTAL === 0 });
    }
    if (days > 60) {
      var w = [];
      for (var i = 0; i < rows.length; i += 7) {
        var c = rows.slice(i, i + 7), last = c[c.length - 1], n = 0, k = false;
        c.forEach(function (x) { n += x.n; k = k || x.kh; });
        w.push({ day: c.length > 1 ? c[0].day + '–' + last.day : String(c[0].day), d0: c[0].day, p1: c[0].p1, p2: last.p2, n: n, from: c[0].from, to: last.to, j1: c[0].j1, j2: last.j2, kh: k });
      }
      return { rows: w, weekly: true };
    }
    rows.forEach(function (r) { r.d0 = r.day; });
    return { rows: rows, weekly: false };
  }

  function dateOf(d0) {
    var v = $('f-date') && $('f-date').value;
    if (!v) return '';
    var dt = new Date(v + 'T12:00:00'); dt.setDate(dt.getDate() + d0 - 1);
    return dt.toLocaleDateString(EN ? 'en-GB' : 'ar-EG', { weekday: 'short', day: 'numeric', month: 'short' });
  }

  function renderKhatma() {
    var days = Math.max(1, Math.min(730, parseInt($('f-days').value, 10) || 30));
    var kh = parseInt($('f-kh').value, 10) || 1;
    var start = Math.max(1, Math.min(604, parseInt($('f-start').value, 10) || 1));
    var ppd = TOTAL * kh / days, m = ppd * 2;
    $('st-ppd').textContent = num(ppd);
    $('st-juz').textContent = num(30 * kh / days);
    $('st-min').textContent = m > 10 ? Math.ceil(m / 5) * 5 : Math.ceil(m);
    $('st-pray').textContent = num(ppd / 5);
    var res = khatmaRows(days, kh, start), hasDate = !!$('f-date').value;
    document.querySelectorAll('.c-date').forEach(function (c) { c.hidden = !hasDate; });
    var html = '';
    res.rows.forEach(function (r) {
      html += '<tr' + (r.kh ? ' class="khatm"' : '') + '><td class="pl-noprint"><input type="checkbox" aria-label="' + (EN ? 'Done ' : 'تم ') + r.day + '"></td>' +
        '<td><bdi dir="ltr">' + r.day + '</bdi></td><td class="c-date"' + (hasDate ? '' : ' hidden') + '>' + esc(dateOf(r.d0)) + '</td>' +
        '<td><bdi dir="ltr">' + r.p1 + '–' + r.p2 + '</bdi> <span class="pl-note">(' + r.n + ')</span></td>' +
        '<td class="ref">' + esc(ref(r.from)) + '</td><td class="ref">' + esc(ref(r.to)) + (r.kh ? '<span class="pl-badge">' + (EN ? 'Khatam ✓' : 'ختمة ✓') + '</span>' : '') + '</td>' +
        '<td><bdi dir="ltr">' + (r.j1 === r.j2 ? r.j1 : r.j1 + '–' + r.j2) + '</bdi></td></tr>';
    });
    tbody.innerHTML = html;
    var t = $('tbl-title');
    if (t) t.textContent = res.weekly ? (EN ? 'Week-by-week schedule' : 'الجدول أسبوعًا بأسبوع') : (EN ? 'Day-by-day schedule' : 'الجدول يومًا بيوم');
    state.key = cfg.key + ':' + days + ':' + kh + ':' + start;
    state.rows = res.rows;
    setParams({ days: days, kh: kh, start: start === 1 ? null : start, date: $('f-date').value || null });
  }

  /* ------------------------------------------------ الحفظ */
  function hifzOrder(dir) {
    var o = [], p;
    if (dir === 'start') { for (p = 1; p <= TOTAL; p++) o.push(p); return o; }
    for (var j = 30; j >= 1; j--) {
      var a = D.juz[j - 1], b = j < 30 ? D.juz[j] - 1 : TOTAL;
      for (p = a; p <= b; p++) o.push(p);
    }
    return o;
  }
  function renderHifz() {
    var years = parseInt($('f-years').value, 10) || 3, dpw = parseInt($('f-dpw').value, 10) || 5, dir = $('f-dir').value;
    var ppd = TOTAL / (years * 52 * dpw);
    $('st-ppd').textContent = num(ppd);
    $('st-lines').textContent = Math.round(ppd * 15);
    $('st-week').textContent = num(ppd * dpw);
    $('st-min').textContent = Math.min(90, Math.max(20, Math.round(ppd * 25 / 5) * 5));
    var months = years * 12, order = hifzOrder(dir), html = '', rows = [];
    for (var m = 0; m < months; m++) {
      var a = Math.round(m * TOTAL / months), b = Math.round((m + 1) * TOTAL / months), seg = order.slice(a, b);
      if (!seg.length) continue;
      var runs = [], cur = [seg[0]];
      for (var i = 1; i < seg.length; i++) { if (seg[i] === cur[cur.length - 1] + 1) cur.push(seg[i]); else { runs.push(cur); cur = [seg[i]]; } }
      runs.push(cur);
      var cell = runs.map(function (r) {
        var f = ref(D.pages[r[0] - 1]), t = ref(pageEnd(r[r.length - 1])), j = juzOf(r[0]), j2 = juzOf(r[r.length - 1]);
        return '<div class="ref">' + (EN ? 'Juz ' + j + (j2 !== j ? '–' + j2 : '') + ': ' + esc(f) + ' → ' + esc(t) : (j2 !== j ? 'الأجزاء <bdi dir="ltr">' + j + '–' + j2 + '</bdi>' : 'الجزء ' + j) + ': من ' + esc(f) + ' إلى ' + esc(t)) +
          ' <span class="pl-note">(' + (EN ? 'p. ' : 'ص ') + '<bdi dir="ltr">' + r[0] + '–' + r[r.length - 1] + '</bdi>)</span></div>';
      }).join('');
      rows.push(m + 1);
      html += '<tr><td class="pl-noprint"><input type="checkbox" aria-label="' + (EN ? 'Done ' : 'تم ') + (m + 1) + '"></td><td>' + (m + 1) + '</td><td>' + cell + '</td><td>' + seg.length + '</td><td>' + Math.round(100 * b / TOTAL) + '%</td></tr>';
    }
    tbody.innerHTML = html;
    state.key = cfg.key + ':' + years + ':' + dpw + ':' + dir;
    state.rows = rows;
    setParams({ years: years, dpw: dpw === 5 ? null : dpw, dir: dir === 'end' ? null : dir });
  }

  /* ------------------------------------------------ التقدم + الرابط */
  var state = { key: '', rows: [] };
  function bindChecks() {
    var saved = store('planner:' + state.key) || [];
    var boxes = tbody.querySelectorAll('input[type=checkbox]');
    boxes.forEach(function (b, i) {
      b.checked = saved.indexOf(i) >= 0;
      b.closest('tr').classList.toggle('done', b.checked);
      b.addEventListener('change', function () {
        var s = store('planner:' + state.key) || [];
        if (b.checked) { if (s.indexOf(i) < 0) s.push(i); } else s = s.filter(function (x) { return x !== i; });
        store('planner:' + state.key, s);
        b.closest('tr').classList.toggle('done', b.checked);
        progress();
      });
    });
    progress();
  }
  function progress() {
    var boxes = tbody.querySelectorAll('input[type=checkbox]'), n = 0;
    boxes.forEach(function (b) { if (b.checked) n++; });
    var pct = boxes.length ? Math.round(100 * n / boxes.length) : 0;
    $('p-bar').style.width = pct + '%';
    if (n) $('p-txt').textContent = (EN ? 'Completed: ' : 'أنجزت: ') + n + ' / ' + boxes.length + ' (' + pct + '%)';
  }
  function setParams(obj) {
    var u = new URL(location.href);
    Object.keys(obj).forEach(function (k) { if (obj[k] === null || obj[k] === undefined || obj[k] === '') u.searchParams.delete(k); else u.searchParams.set(k, obj[k]); });
    history.replaceState(null, '', u.pathname + (u.search || ''));
    var h1 = document.querySelector('h1').textContent.trim();
    $('a-wa').href = 'https://wa.me/?text=' + encodeURIComponent(h1 + '\n' + location.origin + u.pathname + u.search);
  }
  function render() { (cfg.mode === 'khatma' ? renderKhatma : renderHifz)(); bindChecks(); }

  /* ------------------------------------------------ تقويم (ics) */
  function ics() {
    var dv = $('f-date').value;
    if (!dv) { var t = new Date(); dv = t.toISOString().slice(0, 10); $('f-date').value = dv; render(); }
    var days = parseInt($('f-days').value, 10) || 30, kh = parseInt($('f-kh').value, 10) || 1, start = parseInt($('f-start').value, 10) || 1;
    var daily = khatmaRows(Math.min(days, 730), kh, start);
    var all = days > 60 ? (function () { var r = [], total = TOTAL * kh; for (var d = 0; d < days; d++) { var a = Math.round(d * total / days), b = Math.round((d + 1) * total / days); if (b > a) { var p1 = (start - 1 + a) % TOTAL + 1, p2 = (start - 1 + b - 1) % TOTAL + 1; r.push({ d0: d + 1, p1: p1, p2: p2, from: D.pages[p1 - 1], to: pageEnd(p2) }); } } return r; })() : daily.rows;
    var lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//alagme.com//Khatma//AR', 'CALSCALE:GREGORIAN'];
    var stamp = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z';
    all.forEach(function (r) {
      var dt = new Date(dv + 'T12:00:00'); dt.setDate(dt.getDate() + r.d0 - 1);
      var ymd = dt.getFullYear() + String(dt.getMonth() + 1).padStart(2, '0') + String(dt.getDate()).padStart(2, '0');
      var sum = (EN ? 'Quran: pages ' : 'ورد القرآن: صفحات ') + r.p1 + '–' + r.p2;
      var desc = (EN ? 'From ' : 'من ') + ref(r.from) + (EN ? ' to ' : ' إلى ') + ref(r.to) + ' — alagme.com';
      lines.push('BEGIN:VEVENT', 'UID:khatma-' + ymd + '-' + r.d0 + '@alagme.com', 'DTSTAMP:' + stamp,
        'DTSTART:' + ymd + 'T200000', 'DURATION:PT30M', 'SUMMARY:' + sum, 'DESCRIPTION:' + desc,
        'BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:' + sum, 'TRIGGER:-PT0M', 'END:VALARM', 'END:VEVENT');
    });
    lines.push('END:VCALENDAR');
    var blob = new Blob([lines.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = EN ? 'quran-khatam-plan.ics' : 'khatma-plan.ics';
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  /* ------------------------------------------------ تشغيل */
  var q = new URLSearchParams(location.search);
  if (cfg.mode === 'khatma') {
    if (q.get('days')) $('f-days').value = q.get('days');
    if (q.get('kh')) $('f-kh').value = q.get('kh');
    if (q.get('start')) $('f-start').value = q.get('start');
    if (q.get('date')) $('f-date').value = q.get('date');
    ['f-days', 'f-kh', 'f-start', 'f-date'].forEach(function (id) { $(id).addEventListener('change', render); });
    $('f-days').addEventListener('input', function () { if (this.value) render(); });
    $('a-ics').addEventListener('click', ics);
  } else {
    if (q.get('years')) $('f-years').value = q.get('years');
    if (q.get('dpw')) $('f-dpw').value = q.get('dpw');
    if (q.get('dir')) $('f-dir').value = q.get('dir');
    ['f-years', 'f-dpw', 'f-dir'].forEach(function (id) { $(id).addEventListener('change', render); });
  }
  $('a-print').addEventListener('click', function () { window.print(); });
  $('a-copy').addEventListener('click', function () {
    var b = this, old = b.textContent;
    (navigator.clipboard ? navigator.clipboard.writeText(location.href) : Promise.reject()).then(function () {
      b.textContent = EN ? '✓ Link copied' : '✓ تم نسخ الرابط'; setTimeout(function () { b.textContent = old; }, 2000);
    }).catch(function () { window.prompt(EN ? 'Copy this link:' : 'انسخ الرابط:', location.href); });
  });
  render();
})();
