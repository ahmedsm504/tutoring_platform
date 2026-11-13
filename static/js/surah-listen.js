/* مشغل تلاوة خفيف جوه المقال: بيشغل السورة آية آية من EveryAyah، ومش بيحمّل أي صوت قبل ما الزائر يدوس تشغيل */
(function () {
  document.querySelectorAll('.surah-listen').forEach(function (box) {
    var s = +box.dataset.surah, count = +box.dataset.count, en = !!box.dataset.en;
    var audio = box.querySelector('.sl-audio'), play = box.querySelector('.sl-play'),
        pos = box.querySelector('.sl-pos'), sel = box.querySelector('.sl-reciter');
    var reciter = sel.value, a = (s === 1 || s === 9) ? 1 : 0, playing = false, started = false;
    try { var saved = localStorage.getItem('sl-reciter'); if (saved && sel.querySelector('option[value="' + saved + '"]')) { sel.value = saved; reciter = saved; } } catch (e) {}
    function pad(n) { return ('00' + n).slice(-3); }
    function label() {
      if (!started) { pos.textContent = ''; return; }
      pos.textContent = a === 0 ? (en ? 'Basmalah' : 'البسملة') : (en ? 'Verse ' + a + ' of ' + count : 'الآية ' + a + ' من ' + count);
    }
    function src() { return 'https://everyayah.com/data/' + reciter + '/' + (a === 0 ? '001001' : pad(s) + pad(a)) + '.mp3'; }
    function load() { audio.src = src(); label(); if (playing) audio.play().catch(function () {}); }
    function setPlaying(v) {
      playing = v; play.setAttribute('aria-pressed', v ? 'true' : 'false');
      play.textContent = v ? (en ? '❚❚ Pause' : '❚❚ إيقاف') : (en ? '▶ Play' : '▶ تشغيل');
    }
    play.addEventListener('click', function () {
      if (!started) { started = true; setPlaying(true); load(); if (window.gtag) gtag('event', 'surah_listen', {surah: s}); return; }
      if (playing) { audio.pause(); setPlaying(false); } else { setPlaying(true); audio.play().catch(function () {}); }
    });
    box.querySelector('.sl-next').addEventListener('click', function () { if (a < count) { a++; started = true; load(); } });
    box.querySelector('.sl-prev').addEventListener('click', function () { if (a > 1 || (a === 1 && s !== 1 && s !== 9)) { a--; started = true; load(); } });
    sel.addEventListener('change', function () {
      reciter = sel.value; try { localStorage.setItem('sl-reciter', reciter); } catch (e) {}
      if (started) load();
    });
    audio.addEventListener('ended', function () {
      if (a < count) { a++; load(); } else { setPlaying(false); a = (s === 1 || s === 9) ? 1 : 0; started = false; label(); }
    });
    audio.addEventListener('error', function () { if (playing && a < count) { a++; load(); } });
  });
})();
