/* ألعاب الطالب: كلها من آيات السور اللي بيحفظها (جزء عم + سور واجباته) */
(function () {
  'use strict';
  var Q = window.QuranPlayer;
  var cfg = JSON.parse(document.getElementById('games-cfg').textContent);
  var ROUNDS = 6;
  var names = {};
  var AC = window.AudioContext || window.webkitAudioContext, actx = null;

  function beep(f, d, delay, type) {
    try {
      actx = actx || new AC();
      var o = actx.createOscillator(), g = actx.createGain(), t = actx.currentTime + (delay || 0);
      o.type = type || 'sine'; o.frequency.setValueAtTime(f, t);
      g.gain.setValueAtTime(0.18, t); g.gain.exponentialRampToValueAtTime(0.001, t + d);
      o.connect(g); g.connect(actx.destination); o.start(t); o.stop(t + d + 0.02);
    } catch (e) {}
  }
  var sfx = {
    right: function () { beep(660, .12); beep(880, .18, .1); },
    wrong: function () { beep(220, .25, 0, 'triangle'); },
    win: function () { [523, 659, 784, 1046].forEach(function (f, i) { beep(f, .2, i * .12); }); },
    tap: function () { beep(520, .05, 0, 'square'); }
  };
  function shuffle(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  function pick(a) { return a[Math.floor(Math.random() * a.length)]; }
  function words(v) { return v.split(/\s+/).filter(Boolean); }
  function csrf() { var m = document.cookie.match(/csrftoken=([^;]+)/); return m ? m[1] : (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value; }

  function award(points, detail) {
    return fetch(cfg.score_url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      body: JSON.stringify({ kind: 'game', points: points, detail: detail }) })
      .then(function (r) { return r.json(); }).catch(function () { return { added: 0 }; });
  }

  // -------- إطار مشترك لكل لعبة: جولات، نقاط، شاشة النهاية
  var stage = document.getElementById('g-stage'), hub = document.getElementById('g-hub');
  var body = stage.querySelector('.g-body'), titleEl = stage.querySelector('.g-title');
  var roundEl = stage.querySelector('.g-round'), scoreEl = stage.querySelector('.g-pts');
  var state = null;

  function surahPool() {
    var sel = document.getElementById('g-surah');
    return sel && sel.value ? [+sel.value] : cfg.pool;
  }
  function randomAyah(minW, maxW, tries) {
    tries = tries || 0;
    var s = pick(surahPool());
    return Q.loadSurah(s).then(function (d) {
      names[d.id] = d.name;
      var cands = [];
      d.verses.forEach(function (v, i) { var n = words(v).length; if (n >= (minW || 1) && n <= (maxW || 99)) cands.push(i); });
      if (!cands.length) { if (tries > 6) throw new Error('no'); return randomAyah(minW, maxW, tries + 1); }
      var i = pick(cands);
      return { s: d.id, a: i + 1, text: d.verses[i], data: d };
    });
  }

  function start(game) {
    state = { game: game, round: 0, score: 0 };
    titleEl.textContent = game.title;
    hub.style.display = 'none'; stage.classList.add('on');
    window.scrollTo({ top: stage.offsetTop - 80, behavior: 'smooth' });
    nextRound();
  }
  function nextRound() {
    if (state.round >= ROUNDS) return end();
    state.round++; state.locked = false;
    roundEl.textContent = 'جولة ' + Q.arNum(state.round) + ' / ' + Q.arNum(ROUNDS);
    scoreEl.textContent = '⭐ ' + Q.arNum(state.score);
    // كل جولة في div جديد: لو جولة قديمة اتأخرت في التحميل بتكتب في حاجة مش ظاهرة
    var box = document.createElement('div'); box.innerHTML = '<p class="g-msg">⏳</p>';
    body.replaceChildren(box);
    var cur = state;
    state.game.round(box).catch(function () { if (state === cur) box.innerHTML = '<p class="g-msg">تعذّر التحميل، تأكد من الإنترنت.</p>'; });
  }
  function result(ok, msgEl, extra) {
    if (state.locked) return; state.locked = true;
    if (ok) { state.score++; sfx.right(); if (window.fireConfetti) window.fireConfetti({ particleCount: 35, spread: 55 }); }
    else sfx.wrong();
    scoreEl.textContent = '⭐ ' + Q.arNum(state.score);
    if (msgEl) msgEl.innerHTML = (ok ? pick(['برافو! 🌟', 'ممتاز! 👏', 'ما شاء الله! 🎉', 'شاطر جدًا! ⭐']) : 'معلش، الإجابة الصح باللون الأخضر 💚') + (extra || '');
    var cur = state;
    setTimeout(function () { if (state === cur) nextRound(); }, ok ? 1100 : 2200);
  }
  function end() {
    var pts = Math.min(10, state.score * 2), stars = state.score >= ROUNDS ? 3 : state.score >= ROUNDS * .6 ? 2 : state.score > 0 ? 1 : 0;
    body.innerHTML = '<div class="g-end"><div class="big">' + (['😅', '⭐', '⭐⭐', '⭐⭐⭐'][stars]) + '</div>' +
      '<h2>' + (stars === 3 ? 'عبقري! كل الإجابات صح' : stars === 2 ? 'شغل جميل جدًا!' : stars === 1 ? 'كويس، جرّب تاني وهتبقى أحسن' : 'ولا يهمك، جرّب تاني!') + '</h2>' +
      '<p>' + Q.arNum(state.score) + ' من ' + Q.arNum(ROUNDS) + ' إجابات صح</p><p class="g-msg" id="g-award"></p>' +
      '<div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap"><button class="btn btn-primary btn-big" id="g-again">العب تاني 🔁</button>' +
      '<button class="btn btn-outline btn-big" id="g-back">ألعاب تانية 🎮</button></div></div>';
    if (stars >= 2) { sfx.win(); if (window.fireConfetti) { window.fireConfetti({ particleCount: 140, spread: 100 }); } }
    var g = state.game;
    document.getElementById('g-again').onclick = function () { start(g); };
    document.getElementById('g-back').onclick = back;
    if (pts > 0) award(pts, g.id).then(function (r) {
      var el = document.getElementById('g-award');
      if (el) el.textContent = r.added ? ('+' + Q.arNum(r.added) + ' نجمة اتضافت لرصيدك ✨') : 'وصلت لأقصى نجوم ألعاب النهارده، كمّل بكرة 🌙';
      var tot = document.querySelector('.js-total'); if (tot && r.total != null) tot.textContent = Q.arNum(r.total);
    });
  }
  function back() { state = null; stage.classList.remove('on'); hub.style.display = ''; var a = document.querySelector('audio.g-audio'); if (a) a.pause(); }
  stage.querySelector('.g-exit').onclick = back;

  function options(box, list, correct, cls, onPick) {
    var wrap = document.createElement('div'); wrap.className = 'g-opts';
    list.forEach(function (o) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'g-opt ' + (cls || ''); b.textContent = o;
      b.onclick = function () {
        if (state.locked) return;
        var ok = o === correct;
        b.classList.add(ok ? 'right' : 'wrong');
        if (!ok) wrap.querySelectorAll('.g-opt').forEach(function (x) { if (x.textContent === correct) x.classList.add('right'); });
        onPick(ok);
      };
      wrap.appendChild(b);
    });
    box.appendChild(wrap);
  }
  function msg(box) { var m = document.createElement('p'); m.className = 'g-msg'; box.appendChild(m); return m; }
  function ref(x) { return ' <small style="display:block;font-weight:600;color:var(--ink-muted)">سورة ' + x.data.name + ' · آية ' + Q.arNum(x.a) + '</small>'; }

  // -------- الألعاب
  var GAMES = {
    arrange: { id: 'arrange', title: '🧩 رتّب كلمات الآية', round: function (box) {
      return randomAyah(3, 8).then(function (x) {
        var w = words(x.text), order = shuffle(w.map(function (_, i) { return i; }));
        if (order.every(function (v, i) { return v === i; })) order.reverse();
        box.innerHTML = '<p style="text-align:center;margin:0 0 8px;color:var(--ink-muted);font-weight:700">سورة ' + x.data.name + ' — اضغط على الكلمات بالترتيب الصح</p>';
        var ans = document.createElement('div'); ans.className = 'g-words g-ans';
        var bank = document.createElement('div'); bank.className = 'g-words';
        var built = [];
        order.forEach(function (i) {
          var b = document.createElement('button'); b.type = 'button'; b.className = 'g-word'; b.textContent = w[i];
          b.onclick = function () {
            if (state.locked || b.classList.contains('used')) return;
            sfx.tap(); b.classList.add('used'); built.push(i);
            var c = document.createElement('button'); c.type = 'button'; c.className = 'g-word'; c.textContent = w[i];
            c.onclick = function () { if (state.locked) return; built.splice(built.indexOf(i), 1); c.remove(); b.classList.remove('used'); };
            ans.appendChild(c);
            if (built.length === w.length) {
              var ok = built.every(function (v, k) { return w[v] === w[k]; });
              if (!ok) ans.insertAdjacentHTML('afterend', '<div class="g-q" style="font-size:1.2rem">' + x.text + '</div>');
              result(ok, m, ref(x));
            }
          };
          bank.appendChild(b);
        });
        box.appendChild(ans); box.appendChild(bank);
        var m = msg(box);
      });
    } },
    complete: { id: 'complete', title: '✍️ كمّل الكلمة الناقصة', round: function (box) {
      return randomAyah(3, 14).then(function (x) {
        var w = words(x.text), k = Math.random() < .55 ? w.length - 1 : Math.floor(Math.random() * w.length), correct = w[k];
        var pool = [];
        x.data.verses.forEach(function (v) { words(v).forEach(function (t) { if (t !== correct && pool.indexOf(t) < 0) pool.push(t); }); });
        var opts = shuffle([correct].concat(shuffle(pool).slice(0, 3)));
        box.innerHTML = '<div class="g-q">' + w.map(function (t, i) { return i === k ? '<span class="blank">؟</span>' : t; }).join(' ') + '</div>';
        var m;
        options(box, opts, correct, '', function (ok) {
          box.querySelector('.blank').textContent = correct; result(ok, m, ref(x));
        });
        m = msg(box);
      });
    } },
    surah: { id: 'surah', title: '🔎 الآية دي من أي سورة؟', round: function (box) {
      if (surahPool().length < 2) { return Promise.resolve(box.innerHTML = '<p class="g-msg">اللعبة دي محتاجة "كل السور" من القائمة فوق.</p>'); }
      return randomAyah(2, 30).then(function (x) {
        var others = shuffle(cfg.pool.filter(function (s) { return s !== x.s; })).slice(0, 3);
        return Promise.all(others.map(Q.loadSurah)).then(function (ds) {
          var opts = shuffle([x.data.name].concat(ds.map(function (d) { return d.name; })));
          box.innerHTML = '<div class="g-q">' + x.text + '</div>';
          var m;
          options(box, opts, x.data.name, 'sans', function (ok) { result(ok, m, ref(x)); });
          m = msg(box);
        });
      });
    } },
    nextayah: { id: 'nextayah', title: '➡️ إيه الآية اللي بعدها؟', round: function (box) {
      return randomAyah(1, 40).then(function (x) {
        if (x.a >= x.data.verses.length) return GAMES.nextayah.round(box);
        var correct = x.data.verses[x.a];
        var pool = x.data.verses.filter(function (v, i) { return i !== x.a && i !== x.a - 1; });
        var opts = shuffle([correct].concat(shuffle(pool).slice(0, 2)));
        box.innerHTML = '<div class="g-q">' + x.text + ' <span class="ayah-num">' + Q.arNum(x.a) + '</span></div><p style="text-align:center;font-weight:700;margin:0 0 8px">اختار الآية رقم ' + Q.arNum(x.a + 1) + ':</p>';
        var m;
        options(box, opts, correct, '', function (ok) { result(ok, m, ''); });
        m = msg(box);
      });
    } },
    listen: { id: 'listen', title: '🎧 اسمع وخمّن السورة', round: function (box) {
      return randomAyah(1, 40).then(function (x) {
        var pool = cfg.pool.length > 1 ? cfg.pool : cfg.all_short;
        var others = shuffle(pool.filter(function (s) { return s !== x.s; })).slice(0, 3);
        return Promise.all(others.map(Q.loadSurah)).then(function (ds) {
          var opts = shuffle([x.data.name].concat(ds.map(function (d) { return d.name; })));
          box.innerHTML = '<div style="text-align:center;margin-bottom:12px"><button type="button" class="btn btn-primary btn-big g-playbtn">▶ اسمع الآية</button></div>';
          var a = document.querySelector('audio.g-audio') || document.body.appendChild(Object.assign(document.createElement('audio'), { className: 'g-audio' }));
          a.src = Q.audioUrl(cfg.reciter, x.s, x.a);
          var p = a.play(); if (p && p.catch) p.catch(function () {});
          box.querySelector('.g-playbtn').onclick = function () { a.currentTime = 0; a.play(); };
          var m;
          options(box, opts, x.data.name, 'sans', function (ok) { result(ok, m, '<div class="g-q" style="font-size:1.2rem;margin-top:8px">' + x.text + '</div>'); });
          m = msg(box);
        });
      });
    } },
    letters: { id: 'letters', title: '🔤 ذاكرة الحروف', round: function (box) {
      // لعبة ذاكرة: كل حرف مع اسمه. الجولة الواحدة = لوحة كاملة، فبنخلّيها جولة واحدة بس
      var L = shuffle([['ب', 'باء'], ['ت', 'تاء'], ['ث', 'ثاء'], ['ج', 'جيم'], ['ح', 'حاء'], ['خ', 'خاء'], ['د', 'دال'], ['ذ', 'ذال'], ['ر', 'راء'], ['ز', 'زاي'], ['س', 'سين'], ['ش', 'شين'], ['ص', 'صاد'], ['ض', 'ضاد'], ['ط', 'طاء'], ['ظ', 'ظاء'], ['ع', 'عين'], ['غ', 'غين'], ['ف', 'فاء'], ['ق', 'قاف'], ['ك', 'كاف'], ['ل', 'لام'], ['م', 'ميم'], ['ن', 'نون'], ['هـ', 'هاء'], ['و', 'واو'], ['ي', 'ياء']]).slice(0, 6);
      var cards = shuffle(L.reduce(function (acc, p, i) { acc.push({ t: p[0], k: i }, { t: p[1], k: i }); return acc; }, []));
      box.innerHTML = '<p style="text-align:center;font-weight:700;margin:0 0 10px">لاقي كل حرف مع اسمه 🧠</p>';
      var grid = document.createElement('div'); grid.className = 'g-mem'; box.appendChild(grid);
      var open = [], done = 0, moves = 0, m;
      cards.forEach(function (c) {
        var b = document.createElement('button'); b.type = 'button'; b.className = 'g-tile'; b.textContent = c.t; b.style.fontSize = c.t.length > 2 ? 'clamp(1.1rem,4vw,1.6rem)' : '';
        b.onclick = function () {
          if (b.classList.contains('open') || b.classList.contains('done') || open.length === 2) return;
          sfx.tap(); b.classList.add('open'); open.push([b, c]);
          if (open.length === 2) {
            moves++;
            var A = open[0], B = open[1];
            if (A[1].k === B[1].k) { A[0].classList.add('done'); B[0].classList.add('done'); open = []; done++; sfx.right();
              if (done === L.length) { state.score = Math.max(1, ROUNDS - Math.max(0, moves - L.length - 2)); state.round = ROUNDS; m.textContent = 'خلصتها في ' + Q.arNum(moves) + ' محاولة 🎉'; var cur = state; setTimeout(function () { if (state === cur) end(); }, 1200); }
            } else setTimeout(function () { A[0].classList.remove('open'); B[0].classList.remove('open'); open = []; }, 800);
          }
        };
        grid.appendChild(b);
      });
      m = msg(box);
      state.round = ROUNDS; roundEl.textContent = 'لوحة واحدة';
      return Promise.resolve();
    } }
  };

  document.querySelectorAll('[data-game]').forEach(function (b) { b.onclick = function () { start(GAMES[b.dataset.game]); }; });
})();
