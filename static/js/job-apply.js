/* نموذج التقديم للوظائف: خطوات + حفظ تلقائي + تسجيل صوتي + ضغط الصور + رفع بنسبة تقدم */
(function () {
  'use strict';
  var form = document.getElementById('ja-form');
  if (!form) return;
  var steps = Array.prototype.slice.call(form.querySelectorAll('.ja-step'));
  var nav = Array.prototype.slice.call(document.querySelectorAll('.ja-steps-nav li'));
  var topErr = document.getElementById('ja-top-err');
  var KEY = 'jobapply:' + (form.dataset.slug || 'job');
  var cur = 0;
  var store = {}; // name -> [File|Blob] (صور/ملفات) أو Blob (صوت)
  var AR = { '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9' };
  function digits(s) { return String(s || '').replace(/[٠-٩]/g, function (d) { return AR[d]; }).trim(); }
  function ls(k, v) { try { if (v === undefined) return JSON.parse(localStorage.getItem(k) || 'null'); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, JSON.stringify(v)); } catch (e) { return null; } }

  /* ---------------- الخطوات */
  function show(i, scroll) {
    cur = Math.max(0, Math.min(steps.length - 1, i));
    steps.forEach(function (s, k) { s.classList.toggle('on', k === cur); });
    nav.forEach(function (n, k) { n.classList.toggle('on', k === cur); n.classList.toggle('ok', k < cur); });
    if (scroll !== false) document.getElementById('apply').scrollIntoView({ behavior: 'smooth', block: 'start' });
    var s = ls(KEY) || {}; s.__step = cur; ls(KEY, s);
  }
  function fieldVal(box) {
    var t = box.dataset.type, name = box.dataset.name;
    if (t === 'agree') { var c = box.querySelector('input'); return c && c.checked ? 'on' : ''; }
    if (t === 'radio' || t === 'yesno') { var r = box.querySelector('input:checked'); return r ? r.value : ''; }
    if (t === 'checkboxes') return box.querySelectorAll('input:checked').length ? 'x' : '';
    if (t === 'files') return (store[name] || []).length ? 'x' : '';
    if (t === 'audio') return store[name] ? 'x' : '';
    var el = box.querySelector('input,select,textarea'); return el ? el.value.trim() : '';
  }
  function setErr(box, msg) {
    var e = box.querySelector('.err'); if (e) e.textContent = msg || '';
    box.classList.toggle('has-err', !!msg);
  }
  function check(box) {
    var t = box.dataset.type, v = fieldVal(box), d = box.dataset, msg = '';
    if (!v) { if (d.req) msg = t === 'agree' ? (d.msg || 'من فضلك وافقي على هذا الشرط للمتابعة.') : (t === 'audio' ? 'من فضلك سجّلي أو ارفعي الملف الصوتي.' : (t === 'files' ? 'من فضلك ارفعي الملف المطلوب.' : (['radio', 'yesno', 'select', 'checkboxes'].indexOf(t) >= 0 ? 'من فضلك اختاري إجابة.' : 'هذا الحقل مطلوب.'))); }
    else if (t === 'number') {
      var m = digits(v).match(/\d+/), n = m ? parseInt(m[0], 10) : NaN;
      if (isNaN(n) || (d.min !== undefined && n < +d.min) || (d.max !== undefined && n > +d.max)) msg = (!isNaN(n) && d.msg) ? d.msg : 'اكتبي رقمًا صحيحًا بالأرقام.';
    } else if (t === 'phone') {
      var p = digits(v).replace(/[\s\-()]/g, '').replace(/^00/, '+');
      if (!/^\+?\d{9,15}$/.test(p)) msg = 'اكتبي رقمًا صحيحًا (مثال: 01012345678).';
    } else if (d.words && v.split(/\s+/).length < +d.words) msg = +d.words === 3 ? 'من فضلك اكتبي الاسم ثلاثيًا.' : 'اكتبي ' + d.words + ' كلمات على الأقل.';
    else if (d.minlen && v.length < +d.minlen) msg = 'من فضلك اكتبي إجابة أكثر تفصيلًا (' + v.length + ' / ' + d.minlen + ' حرفًا).';
    if (!msg && d.must && v && v !== d.must) msg = d.reject || 'هذا شرط أساسي.';
    setErr(box, msg);
    return !msg;
  }
  function checkStep(i) {
    var ok = true, first = null;
    steps[i].querySelectorAll('.field[data-name]').forEach(function (b) { if (!check(b)) { ok = false; first = first || b; } });
    if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return ok;
  }
  form.addEventListener('click', function (e) {
    if (e.target.closest('[data-next]')) { if (checkStep(cur)) { topErr.hidden = true; show(cur + 1); } }
    else if (e.target.closest('[data-prev]')) show(cur - 1);
  });
  form.addEventListener('change', function (e) { var b = e.target.closest('.field[data-name]'); if (b && b.classList.contains('has-err')) check(b); save(); });
  form.addEventListener('input', function (e) { var b = e.target.closest('.field[data-name]'); if (b && b.classList.contains('has-err')) check(b); save(); });

  /* ---------------- حفظ تلقائي (النصوص والاختيارات فقط) */
  var savedNote = document.getElementById('ja-saved'), saveT;
  function save() {
    clearTimeout(saveT);
    saveT = setTimeout(function () {
      var s = { __step: cur };
      Array.prototype.forEach.call(form.elements, function (el) {
        if (!el.name || el.type === 'file' || el.type === 'hidden' || el.name === 'website' || el.name === 'csrfmiddlewaretoken') return;
        if (el.type === 'radio') { if (el.checked) s[el.name] = el.value; }
        else if (el.type === 'checkbox') { if (el.checked) (s[el.name] = s[el.name] || []).push(el.value); }
        else s[el.name] = el.value;
      });
      ls(KEY, s);
      if (savedNote) savedNote.hidden = false;
    }, 400);
  }
  function restore() {
    var s = ls(KEY); if (!s) return;
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name || !(el.name in s) || el.type === 'file') return;
      var v = s[el.name];
      if (el.type === 'radio') el.checked = el.value === v;
      else if (el.type === 'checkbox') el.checked = Array.isArray(v) && v.indexOf(el.value) >= 0;
      else if (!el.value) el.value = v;
    });
    if (savedNote) savedNote.hidden = false;
    if (s.__step) show(s.__step, false);
  }

  /* ---------------- الصور والملفات */
  function compress(file) {
    if (!/^image\/(jpeg|png|webp)$/.test(file.type) || file.size < 450 * 1024 || !window.createImageBitmap) return Promise.resolve(file);
    return createImageBitmap(file).then(function (bmp) {
      var max = 1800, r = Math.min(1, max / Math.max(bmp.width, bmp.height));
      var c = document.createElement('canvas'); c.width = Math.round(bmp.width * r); c.height = Math.round(bmp.height * r);
      c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
      return new Promise(function (res) { c.toBlob(function (b) { res(b && b.size < file.size ? new File([b], file.name.replace(/\.\w+$/, '') + '.jpg', { type: 'image/jpeg' }) : file); }, 'image/jpeg', 0.82); });
    }).catch(function () { return file; });
  }
  function renderThumbs(box) {
    var name = box.dataset.name, wrap = box.querySelector('.ja-thumbs'); if (!wrap) return;
    wrap.innerHTML = '';
    (store[name] || []).forEach(function (f, i) {
      var fig = document.createElement('figure');
      if (/^image\//.test(f.type) && !/heic|heif/.test(f.type)) { var img = document.createElement('img'); img.alt = ''; img.src = URL.createObjectURL(f); fig.appendChild(img); }
      else fig.appendChild(document.createTextNode('📄 ' + f.name));
      var x = document.createElement('button'); x.type = 'button'; x.setAttribute('aria-label', 'حذف'); x.textContent = '×';
      x.onclick = function () { store[name].splice(i, 1); renderThumbs(box); };
      fig.appendChild(x); wrap.appendChild(fig);
    });
  }
  form.querySelectorAll('.field[data-type="files"] input[type=file]').forEach(function (inp) {
    var box = inp.closest('.field'), name = box.dataset.name, max = +box.dataset.maxfiles || 1;
    inp.addEventListener('change', function () {
      var list = Array.prototype.slice.call(inp.files || []);
      inp.value = '';
      Promise.all(list.map(compress)).then(function (files) {
        store[name] = (max === 1 ? [] : (store[name] || [])).concat(files).slice(0, max);
        if (list.length + (store[name].length - files.length) > max) setErr(box, 'أقصى عدد ملفات هنا ' + max + '.'); else check(box);
        renderThumbs(box);
      });
    });
  });

  /* ---------------- الصوت: تسجيل مباشر أو رفع ملف */
  function pickMime() {
    if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) return '';
    var c = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus', 'audio/webm'];
    for (var i = 0; i < c.length; i++) if (MediaRecorder.isTypeSupported(c[i])) return c[i];
    return '';
  }
  function setAudio(box, blob, label) {
    var name = box.dataset.name, out = box.querySelector('.ja-audio');
    store[name] = blob;
    out.innerHTML = '';
    if (!blob) return;
    var a = document.createElement('audio'); a.controls = true; a.src = URL.createObjectURL(blob); out.appendChild(a);
    var s = document.createElement('span'); s.className = 'ja-help'; s.textContent = label; out.appendChild(s);
    var del = document.createElement('button'); del.type = 'button'; del.className = 'ja-linkbtn'; del.textContent = 'حذف';
    del.onclick = function () { setAudio(box, null); }; out.appendChild(del);
    check(box);
  }
  var canRec = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
  form.querySelectorAll('.field[data-type="audio"]').forEach(function (box) {
    var btn = box.querySelector('[data-rec]'), timer = box.querySelector('.ja-timer'), inp = box.querySelector('input[type=file]');
    if (!canRec) box.classList.add('ja-norec');
    inp.addEventListener('change', function () {
      var f = inp.files && inp.files[0]; inp.value = '';
      if (f) setAudio(box, f, 'ملف مرفوع: ' + f.name);
    });
    if (!btn || !canRec) return;
    var rec = null, chunks = [], t0 = 0, tick = null, stream = null;
    function fmt(s) { return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); }
    function stopAll() { if (tick) clearInterval(tick); if (stream) stream.getTracks().forEach(function (t) { t.stop(); }); btn.classList.remove('stop', 'live'); btn.querySelector('span').textContent = 'إعادة التسجيل'; }
    btn.addEventListener('click', function () {
      if (rec && rec.state === 'recording') { rec.stop(); return; }
      navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } }).then(function (s) {
        stream = s; chunks = [];
        var mime = pickMime(), opts = { audioBitsPerSecond: 64000 }; if (mime) opts.mimeType = mime;
        try { rec = new MediaRecorder(s, opts); } catch (e) { rec = new MediaRecorder(s); }
        rec.ondataavailable = function (e) { if (e.data && e.data.size) chunks.push(e.data); };
        rec.onstop = function () {
          stopAll();
          var type = (rec.mimeType || mime || 'audio/webm').split(';')[0];
          var ext = type.indexOf('mp4') >= 0 ? 'm4a' : (type.indexOf('ogg') >= 0 ? 'ogg' : 'webm');
          var blob = new File(chunks, box.dataset.name + '-recording.' + ext, { type: type });
          setAudio(box, blob, 'تسجيل مدته ' + timer.textContent + ' — استمعي له قبل الإرسال');
        };
        rec.start(1000); t0 = Date.now(); timer.textContent = '00:00';
        btn.classList.add('stop', 'live'); btn.querySelector('span').textContent = 'إيقاف التسجيل';
        tick = setInterval(function () { var sec = Math.floor((Date.now() - t0) / 1000); timer.textContent = fmt(sec); if (sec >= 600) rec.stop(); }, 500);
      }).catch(function () {
        setErr(box, 'لم نتمكن من الوصول للميكروفون. اسمحي للمتصفح باستخدام الميكروفون، أو سجّلي من تطبيق التسجيل في هاتفك وارفعي الملف.');
      });
    });
  });

  /* ---------------- الإرسال */
  var prog = document.getElementById('ja-progress'), bar = prog && prog.querySelector('span'), ptxt = document.getElementById('ja-progress-txt');
  var submitBtn = document.getElementById('ja-submit');
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    for (var i = 0; i < steps.length; i++) { if (!checkStep(i)) { show(i); setTimeout(function () { var b = form.querySelector('.ja-step.on .has-err'); if (b) b.scrollIntoView({ block: 'center' }); }, 350); return; } }
    var fd = new FormData(form);
    Object.keys(store).forEach(function (name) {
      fd.delete(name);
      var v = store[name]; if (!v) return;
      (Array.isArray(v) ? v : [v]).forEach(function (f) { fd.append(name, f, f.name || (name + '.bin')); });
    });
    form.querySelectorAll('input[type=file]').forEach(function (inp) { if (!(inp.name in store)) fd.delete(inp.name); });
    var xhr = new XMLHttpRequest();
    xhr.open('POST', form.action);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.upload.onprogress = function (ev) { if (ev.lengthComputable && bar) { var p = Math.round(100 * ev.loaded / ev.total); bar.style.width = p + '%'; ptxt.textContent = 'جارٍ رفع الطلب… ' + p + '%'; if (p >= 100) ptxt.textContent = 'جارٍ الحفظ…'; } };
    xhr.onload = function () {
      var r = null; try { r = JSON.parse(xhr.responseText); } catch (err) { r = null; }
      if (r && r.ok) { ls(KEY, null); location.href = r.redirect; return; }
      submitBtn.disabled = false; prog.classList.remove('on');
      var errs = (r && r.errors) || { __all__: 'حدث خطأ أثناء الإرسال. تأكدي من الإنترنت وحاولي مرة أخرى.' };
      var firstStep = null;
      Object.keys(errs).forEach(function (k) {
        if (k === '__all__') return;
        var box = form.querySelector('.field[data-name="' + k + '"]'); if (!box) return;
        setErr(box, errs[k]);
        var st = steps.indexOf(box.closest('.ja-step')); if (firstStep === null || st < firstStep) firstStep = st;
      });
      topErr.textContent = errs.__all__ || 'من فضلك راجعي الحقول اللي عليها ملاحظة.';
      topErr.hidden = false;
      show(firstStep === null ? cur : firstStep);
    };
    xhr.onerror = function () {
      submitBtn.disabled = false; prog.classList.remove('on');
      topErr.textContent = 'انقطع الاتصال أثناء الرفع. تأكدي من الإنترنت وحاولي مرة أخرى (إجاباتك محفوظة).'; topErr.hidden = false;
    };
    submitBtn.disabled = true; prog.classList.add('on'); bar.style.width = '0'; topErr.hidden = true;
    xhr.send(fd);
  });

  /* ---------------- البداية */
  var serverErr = form.querySelector('.field.has-err');
  if (serverErr) { show(steps.indexOf(serverErr.closest('.ja-step')), false); }
  else restore();
})();
