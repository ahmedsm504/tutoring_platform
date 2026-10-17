/* مشغّل القرآن: آية آية بصوت الشيخ اللي تختاره، مع تكرار ووضع "اختبر حفظك".
   الصوت من everyayah.com (ملف لكل آية)، والنص من static/quran/{n}.json
   الاستخدام: <div class="qp" data-surah="78" data-from="1" data-to="10"><div class="qp-text">...</div></div>
   ثم QuranPlayer.mountAll()  —  الآيات لازم تكون <span class="ayah" data-a="رقم"> أو هتتحمل لوحدها */
(function () {
  'use strict';
  var STORE = 'qp-reciter';
  var BASE = 'https://everyayah.com/data/';
  var STATIC = (document.querySelector('meta[name="static-url"]') || {}).content || '/static/';
  var ARABIC_DIGITS = '٠١٢٣٤٥٦٧٨٩';

  function arNum(n) { return String(n).replace(/\d/g, function (d) { return ARABIC_DIGITS[d]; }); }
  function pad(n) { return ('00' + n).slice(-3); }
  function get(key, def) { try { return localStorage.getItem(key) || def; } catch (e) { return def; } }
  function put(key, v) { try { localStorage.setItem(key, v); } catch (e) {} }
  function el(tag, attrs, html) {
    var e = document.createElement(tag);
    for (var k in (attrs || {})) { if (k === 'class') e.className = attrs[k]; else e.setAttribute(k, attrs[k]); }
    if (html != null) e.innerHTML = html;
    return e;
  }

  var cache = {};
  function loadSurah(n) {
    if (!cache[n]) cache[n] = fetch(STATIC + 'quran/' + n + '.json').then(function (r) { return r.json(); });
    return cache[n];
  }
  function loadIndex() { return loadSurah('index'); }

  function reciters() {
    var node = document.getElementById('qp-reciters');
    try { return JSON.parse(node.textContent); } catch (e) { return [['Husary_128kbps', 'محمود خليل الحصري']]; }
  }

  function renderVerses(box, data, from, to) {
    var frag = document.createDocumentFragment();
    if (from === 1 && data.id !== 1 && data.id !== 9) {
      frag.appendChild(el('p', { class: 'qp-basmala' }, 'بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ'));
    }
    var p = el('p', { class: 'qp-flow', lang: 'ar' });
    for (var i = from; i <= to; i++) {
      var s = el('span', { class: 'ayah', 'data-a': i, tabindex: '0', role: 'button', 'aria-label': 'تشغيل الآية ' + i });
      s.textContent = data.verses[i - 1] + ' ';
      var m = el('span', { class: 'ayah-num', 'aria-hidden': 'true' }, arNum(i));
      s.appendChild(m);
      p.appendChild(s);
      p.appendChild(document.createTextNode(' '));
    }
    frag.appendChild(p);
    box.replaceChildren(frag);
  }

  function Player(root) {
    this.root = root;
    this.surah = +root.dataset.surah || 1;
    this.from = +root.dataset.from || 1;
    this.to = +root.dataset.to || 0;
    this.text = root.querySelector('.qp-text') || root.appendChild(el('div', { class: 'qp-text' }));
    this.reciter = root.dataset.reciter || get(STORE, 'Husary_128kbps');
    this.repeat = 1; this.loop = false; this.rate = 1; this.basmala = true;
    this.queue = []; this.pos = 0; this.rep = 0; this.playing = false;
    this.audio = new Audio(); this.audio.preload = 'auto';
    this.next = new Audio(); this.next.preload = 'auto';
    this.build();
    var self = this;
    if (!this.text.querySelector('.ayah')) this.load(this.surah, this.from, this.to);
    else this.bindAyahs();
    this.audio.addEventListener('ended', function () { self.advance(); });
    this.audio.addEventListener('error', function () {
      if (!self.playing) return;
      self.status('تعذّر تحميل صوت الآية، بنجرّب اللي بعدها…');
      setTimeout(function () { self.advance(true); }, 700);
    });
    this.audio.addEventListener('waiting', function () { self.root.classList.add('qp-loading'); });
    this.audio.addEventListener('playing', function () { self.root.classList.remove('qp-loading'); });
  }

  Player.prototype.build = function () {
    var self = this, opts = reciters().map(function (r) {
      return '<option value="' + r[0] + '"' + (r[0] === self.reciter ? ' selected' : '') + '>' + r[1] + '</option>';
    }).join('');
    var bar = el('div', { class: 'qp-bar' });
    bar.innerHTML =
      '<div class="qp-main">' +
        '<button type="button" class="qp-btn qp-prev" aria-label="الآية السابقة">⏭</button>' +
        '<button type="button" class="qp-btn qp-play" aria-label="تشغيل">▶</button>' +
        '<button type="button" class="qp-btn qp-next" aria-label="الآية التالية">⏮</button>' +
        '<span class="qp-now" aria-live="polite">اضغط ▶ أو اختار أي آية</span>' +
      '</div>' +
      '<div class="qp-opts">' +
        '<label class="qp-opt"><span>الشيخ</span><select class="qp-reciter">' + opts + '</select></label>' +
        '<label class="qp-opt"><span>كرر كل آية</span><select class="qp-repeat"><option>1</option><option>2</option><option>3</option><option>5</option><option>10</option></select></label>' +
        '<label class="qp-opt"><span>السرعة</span><select class="qp-rate"><option value="0.75">بطيء</option><option value="1" selected>عادي</option><option value="1.25">سريع</option></select></label>' +
        '<button type="button" class="qp-chip qp-loop" aria-pressed="false">🔁 كرر المقطع</button>' +
        '<button type="button" class="qp-chip qp-hide" aria-pressed="false">🙈 اختبر حفظك</button>' +
      '</div>';
    this.root.insertBefore(bar, this.root.firstChild);
    this.bar = bar;
    this.$ = function (s) { return bar.querySelector(s); };
    this.$('.qp-play').onclick = function () { self.toggle(); };
    this.$('.qp-prev').onclick = function () { self.jump(-1); };
    this.$('.qp-next').onclick = function () { self.jump(1); };
    this.$('.qp-reciter').onchange = function () {
      self.reciter = this.value; put(STORE, this.value);
      if (self.playing) self.playCurrent();
    };
    this.$('.qp-repeat').onchange = function () { self.repeat = +this.value; };
    this.$('.qp-rate').onchange = function () { self.rate = +this.value; self.audio.playbackRate = self.rate; };
    this.$('.qp-loop').onclick = function () {
      self.loop = !self.loop; this.setAttribute('aria-pressed', self.loop); this.classList.toggle('on', self.loop);
    };
    this.$('.qp-hide').onclick = function () {
      var on = !self.root.classList.contains('qp-hidden');
      self.root.classList.toggle('qp-hidden', on); this.setAttribute('aria-pressed', on); this.classList.toggle('on', on);
      self.text.querySelectorAll('.ayah.shown').forEach(function (a) { a.classList.remove('shown'); });
    };
  };

  Player.prototype.status = function (t) { this.$('.qp-now').textContent = t; };

  Player.prototype.load = function (surah, from, to) {
    var self = this;
    this.stop();
    this.surah = +surah;
    this.text.innerHTML = '<p class="qp-wait">جاري تحميل الآيات…</p>';
    return loadSurah(this.surah).then(function (data) {
      self.data = data;
      self.from = Math.max(1, +from || 1);
      self.to = Math.min(data.verses.length, +to || data.verses.length);
      if (self.from > self.to) self.from = self.to;
      renderVerses(self.text, data, self.from, self.to);
      self.bindAyahs();
      self.status('سورة ' + data.name + ' · اضغط ▶');
      self.root.dispatchEvent(new CustomEvent('quran:loaded', { detail: { surah: self.surah, from: self.from, to: self.to } }));
    }).catch(function () { self.text.innerHTML = '<p class="qp-wait">تعذّر تحميل الآيات. تأكد من الإنترنت.</p>'; });
  };

  Player.prototype.bindAyahs = function () {
    var self = this;
    var nodes = this.text.querySelectorAll('.ayah');
    if (!this.to) this.to = +nodes[nodes.length - 1].dataset.a;
    nodes.forEach(function (n) {
      function go() {
        if (self.root.classList.contains('qp-hidden') && !n.classList.contains('shown')) { n.classList.add('shown'); return; }
        self.start(+n.dataset.a);
      }
      n.addEventListener('click', go);
      n.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } });
    });
  };

  Player.prototype.buildQueue = function (startAyah) {
    var q = [];
    if (this.basmala && startAyah === 1 && this.surah !== 1 && this.surah !== 9) q.push([1, 1, true]);
    for (var a = startAyah; a <= this.to; a++) q.push([this.surah, a, false]);
    return q;
  };

  Player.prototype.url = function (item) { return BASE + this.reciter + '/' + pad(item[0]) + pad(item[1]) + '.mp3'; };

  Player.prototype.start = function (ayah) {
    this.queue = this.buildQueue(ayah || this.from);
    this.pos = 0; this.rep = 0; this.playing = true;
    this.playCurrent();
  };

  Player.prototype.playCurrent = function () {
    var item = this.queue[this.pos];
    if (!item) return this.finish();
    this.audio.src = this.url(item);
    this.audio.playbackRate = this.rate;
    var self = this, p = this.audio.play();
    if (p && p.catch) p.catch(function () { self.playing = false; self.paint(); });
    var nxt = this.queue[this.pos + 1];
    if (nxt) this.next.src = this.url(nxt);
    this.highlight(item[2] ? null : item[1]);
    this.status(item[2] ? 'البسملة' : ('سورة ' + (this.data ? this.data.name : '') + ' · الآية ' + arNum(item[1]) +
      (this.repeat > 1 ? ' · مرة ' + arNum(this.rep + 1) + ' من ' + arNum(this.repeat) : '')));
    this.paint();
  };

  Player.prototype.advance = function (skipRepeat) {
    var item = this.queue[this.pos];
    if (!skipRepeat && item && !item[2] && this.rep + 1 < this.repeat) { this.rep++; return this.playCurrent(); }
    this.rep = 0; this.pos++;
    if (this.pos >= this.queue.length) {
      this.root.dispatchEvent(new CustomEvent('quran:finished', { detail: { surah: this.surah, from: this.from, to: this.to } }));
      if (this.loop) { this.queue = this.buildQueue(this.from).filter(function (x) { return !x[2]; }); this.pos = 0; return this.playCurrent(); }
      return this.finish();
    }
    this.playCurrent();
  };

  Player.prototype.jump = function (d) {
    if (!this.queue.length) return this.start(this.from);
    var item = this.queue[this.pos], a = (item && !item[2] ? item[1] : this.from - 1) + d;
    a = Math.max(this.from, Math.min(this.to, a));
    this.start(a);
  };

  Player.prototype.toggle = function () {
    if (!this.queue.length || this.pos >= this.queue.length) return this.start(this.from);
    if (this.audio.paused) { this.playing = true; this.audio.play(); } else { this.playing = false; this.audio.pause(); }
    this.paint();
  };

  Player.prototype.stop = function () { this.audio.pause(); this.playing = false; this.queue = []; this.pos = 0; this.highlight(null); if (this.bar) this.paint(); };
  Player.prototype.finish = function () { this.playing = false; this.highlight(null); this.status('خلصت التلاوة ✓ — اضغط ▶ للإعادة'); this.queue = []; this.paint(); };

  Player.prototype.paint = function () {
    var b = this.$('.qp-play');
    var on = this.playing && !this.audio.paused;
    b.textContent = on ? '⏸' : '▶'; b.setAttribute('aria-label', on ? 'إيقاف مؤقت' : 'تشغيل');
    this.root.classList.toggle('qp-on', on);
  };

  Player.prototype.highlight = function (a) {
    var cur = this.text.querySelector('.ayah.now');
    if (cur) cur.classList.remove('now');
    if (a == null) return;
    var n = this.text.querySelector('.ayah[data-a="' + a + '"]');
    if (n) {
      n.classList.add('now');
      var r = n.getBoundingClientRect();
      if (r.top < 70 || r.bottom > window.innerHeight - 20) n.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  window.QuranPlayer = {
    mount: function (root) { if (!root._qp) root._qp = new Player(root); return root._qp; },
    mountAll: function () { document.querySelectorAll('.qp').forEach(function (r) { window.QuranPlayer.mount(r); }); },
    loadSurah: loadSurah, loadIndex: loadIndex, arNum: arNum,
    audioUrl: function (reciter, s, a) { return BASE + reciter + '/' + pad(s) + pad(a) + '.mp3'; }
  };
  if (document.readyState !== 'loading') window.QuranPlayer.mountAll();
  else document.addEventListener('DOMContentLoaded', window.QuranPlayer.mountAll);
})();
