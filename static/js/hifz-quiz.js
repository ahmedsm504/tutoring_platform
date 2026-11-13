/* اختبار "إيه الآية اللي بعدها؟" - بيحمّل نص السورة بس لما الزائر يدوس ابدأ */
(function () {
  function shuffle(a) { for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  document.querySelectorAll('.hifz-quiz').forEach(function (box) {
    var en = !!box.dataset.en, verses = null, qs = [], qi = 0, score = 0, TOTAL = 10;
    var body = box.querySelector('.hq-body'), start = box.querySelector('.hq-start'),
        prog = box.querySelector('.hq-progress'), vEl = box.querySelector('.hq-verse'),
        opts = box.querySelector('.hq-options'), fb = box.querySelector('.hq-feedback'), next = box.querySelector('.hq-next');
    function t(ar, e) { return en ? e : ar; }
    function build() {
      var idx = []; for (var i = 0; i < verses.length - 1; i++) idx.push(i);
      qs = shuffle(idx).slice(0, Math.min(TOTAL, idx.length)); qi = 0; score = 0;
    }
    function show() {
      var k = qs[qi], right = k + 1, pool = [];
      for (var i = 0; i < verses.length; i++) if (i !== right && i !== k && verses[i] !== verses[right]) pool.push(i);
      var choices = shuffle([right].concat(shuffle(pool).slice(0, 2)));
      prog.textContent = t('السؤال ' + (qi + 1) + ' من ' + qs.length + ' · النتيجة ' + score, 'Question ' + (qi + 1) + ' of ' + qs.length + ' · Score ' + score);
      vEl.textContent = verses[k] + ' (' + (k + 1) + ')';
      opts.innerHTML = ''; fb.textContent = ''; next.hidden = true;
      choices.forEach(function (c) {
        var b = document.createElement('button'); b.type = 'button'; b.className = 'hq-opt'; b.lang = 'ar'; b.dir = 'rtl';
        b.textContent = verses[c];
        b.addEventListener('click', function () {
          if (!next.hidden) return;
          var ok = c === right; if (ok) score++;
          b.classList.add(ok ? 'ok' : 'bad');
          opts.querySelectorAll('.hq-opt').forEach(function (o, i) { if (choices[i] === right) o.classList.add('ok'); o.disabled = true; });
          fb.textContent = ok ? t('أحسنت! إجابة صحيحة ✓', 'Well done! Correct ✓') : t('الإجابة الصحيحة هي الآية ' + (right + 1) + ' المعلَّمة بالأخضر.', 'The correct answer is verse ' + (right + 1) + ', marked in green.');
          next.textContent = qi + 1 < qs.length ? t('السؤال التالي', 'Next question') : t('شوف النتيجة', 'See your score');
          next.hidden = false;
        });
        opts.appendChild(b);
      });
    }
    function finish() {
      prog.textContent = ''; vEl.textContent = ''; opts.innerHTML = ''; next.hidden = true;
      var pct = Math.round(score / qs.length * 100);
      fb.textContent = t('نتيجتك ' + score + ' من ' + qs.length + ' (' + pct + '%). ', 'Your score: ' + score + ' of ' + qs.length + ' (' + pct + '%). ') +
        (pct >= 80 ? t('حفظك ممتاز، كمّل مراجعة.', 'Excellent memorisation, keep revising.') : t('محتاج مراجعة شوية، اسمع السورة وكرر الآيات وجرب تاني.', 'Some revision needed: listen to the surah, repeat the verses and try again.'));
      start.textContent = t('اختبر نفسك تاني', 'Try again'); start.hidden = false;
      if (window.gtag) gtag('event', 'hifz_quiz_done', {score: pct});
    }
    next.addEventListener('click', function () { qi++; if (qi < qs.length) show(); else finish(); });
    start.addEventListener('click', function () {
      start.hidden = true; body.hidden = false;
      if (verses) { build(); show(); return; }
      fb.textContent = t('جاري التحميل...', 'Loading...');
      fetch(box.dataset.src).then(function (r) { return r.json(); }).then(function (d) { verses = d.verses; build(); show(); })
        .catch(function () { fb.textContent = t('حصل خطأ في التحميل، جرّب تاني.', 'Could not load, please try again.'); start.hidden = false; });
    });
  });
})();
