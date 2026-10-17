/* مسجّل صوت بسيط: بيسجّل من المايك وبيحط التسجيل في input[type=file] عادي جوه الفورم،
   فالفورم يتبعت عادي. لو المتصفح مش بيدعم التسجيل، الطالب يرفع ملف من الموبايل. */
(function () {
  'use strict';
  function fmt(s) { s = Math.floor(s); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function pickMime() {
    var c = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus', 'audio/aac'];
    if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) return '';
    for (var i = 0; i < c.length; i++) if (MediaRecorder.isTypeSupported(c[i])) return c[i];
    return '';
  }

  function mount(box) {
    if (box._rec) return;
    box._rec = true;
    var input = box.querySelector('input[type=file]');
    var btn = box.querySelector('.rec-btn');
    var timer = box.querySelector('.rec-time');
    var hint = box.querySelector('.rec-hint');
    var preview = box.querySelector('.rec-preview');
    var redo = box.querySelector('.rec-redo');
    var bars = box.querySelector('.rec-bars');
    var max = +(box.dataset.max || 600);
    var rec = null, chunks = [], t0 = 0, tick = null, stream = null, analyser = null, raf = null;
    var supported = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder && window.DataTransfer);

    if (!supported) {
      box.classList.add('rec-fallback');
      if (hint) hint.textContent = 'المتصفح ده مش بيسجّل مباشرة — اضغط واختار تسجيل من موبايلك 🎙️';
      return;
    }

    function setFile(blob, type) {
      var ext = type.indexOf('mp4') > -1 ? 'm4a' : type.indexOf('ogg') > -1 ? 'ogg' : type.indexOf('aac') > -1 ? 'aac' : 'webm';
      var f = new File([blob], 'recording-' + Date.now() + '.' + ext, { type: type.split(';')[0] });
      var dt = new DataTransfer(); dt.items.add(f); input.files = dt.files;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function draw() {
      if (!analyser || !bars) return;
      var d = new Uint8Array(analyser.frequencyBinCount); analyser.getByteFrequencyData(d);
      var spans = bars.children;
      for (var i = 0; i < spans.length; i++) {
        var v = d[Math.floor(i * d.length / spans.length / 2)] / 255;
        spans[i].style.transform = 'scaleY(' + Math.max(0.12, v) + ')';
      }
      raf = requestAnimationFrame(draw);
    }

    function start() {
      navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } }).then(function (s) {
        stream = s; chunks = [];
        var mime = pickMime();
        rec = new MediaRecorder(s, mime ? { mimeType: mime } : undefined);
        rec.ondataavailable = function (e) { if (e.data && e.data.size) chunks.push(e.data); };
        rec.onstop = function () {
          var type = rec.mimeType || mime || 'audio/webm';
          var blob = new Blob(chunks, { type: type });
          setFile(blob, type);
          preview.src = URL.createObjectURL(blob);
          box.classList.remove('rec-on'); box.classList.add('rec-done');
          if (hint) hint.textContent = 'اسمع تسجيلك ✓ لو تمام ابعته، أو سجّل تاني';
          stream.getTracks().forEach(function (t) { t.stop(); });
          cancelAnimationFrame(raf); clearInterval(tick);
        };
        try {
          var AC = window.AudioContext || window.webkitAudioContext, ac = new AC();
          analyser = ac.createAnalyser(); analyser.fftSize = 64; ac.createMediaStreamSource(s).connect(analyser); draw();
        } catch (e) {}
        rec.start(1000); t0 = Date.now();
        box.classList.add('rec-on'); box.classList.remove('rec-done');
        if (hint) hint.textContent = 'بيسجّل الآن… اقرأ بهدوء، واضغط ⏹ لما تخلص';
        tick = setInterval(function () {
          var s = (Date.now() - t0) / 1000; timer.textContent = fmt(s);
          if (s >= max) stop();
        }, 250);
      }).catch(function () {
        if (hint) hint.textContent = 'لازم تسمح للموقع يستخدم المايك 🎤 (من علامة القفل جنب العنوان)';
        box.classList.add('rec-fallback');
      });
    }
    function stop() { if (rec && rec.state !== 'inactive') rec.stop(); }

    btn.addEventListener('click', function () { if (rec && rec.state === 'recording') stop(); else start(); });
    if (redo) redo.addEventListener('click', function () {
      input.value = ''; preview.removeAttribute('src'); box.classList.remove('rec-done'); timer.textContent = '0:00';
      if (hint) hint.textContent = 'اضغط على المايك وابدأ التسجيل';
    });
    input.addEventListener('change', function () {
      if (input.files[0] && !box.classList.contains('rec-done')) {
        preview.src = URL.createObjectURL(input.files[0]); box.classList.add('rec-done');
        if (hint) hint.textContent = 'تم اختيار الملف ✓';
      }
    });
  }
  window.mountRecorders = function () { document.querySelectorAll('.rec').forEach(mount); };
  if (document.readyState !== 'loading') window.mountRecorders();
  else document.addEventListener('DOMContentLoaded', window.mountRecorders);
})();
