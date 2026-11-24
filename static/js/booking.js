/* فورم الحجز على خطوتين: (1) الاسم والواتساب بيتسجلوا فورًا كحجز «مش مكتمل»، (2) باقي البيانات.
   من غير جافاسكربت الفورم بيظهر كله عادي. */
(function () {
  var form = document.querySelector('form[data-booking]');
  if (!form) return;
  var en = form.getAttribute('data-lang') === 'en';
  var s1 = form.querySelector('[data-step="1"]'), s2 = form.querySelector('[data-step="2"]');
  var next = form.querySelector('[data-next]'), back = form.querySelector('[data-back]');
  var name = form.querySelector('[name=name]'), phone = form.querySelector('[name=phone]');
  var country = form.querySelector('[name=country]'), token = form.querySelector('[name=booking_token]');
  function cookie(n) { var m = document.cookie.match('(?:^|; )' + n + '=([^;]*)'); return m ? decodeURIComponent(m[1]) : ''; }
  function fillTracking() {
    form.querySelector('[name=trk_first]').value = cookie('al_first');
    form.querySelector('[name=trk_prev]').value = cookie('al_prev');
  }
  var TZ = {
    'Africa/Cairo': ['مصر', 'Egypt'], 'Asia/Riyadh': ['السعودية', 'Saudi Arabia'], 'Asia/Dubai': ['الإمارات', 'UAE'],
    'Asia/Kuwait': ['الكويت', 'Kuwait'], 'Asia/Qatar': ['قطر', 'Qatar'], 'Asia/Bahrain': ['البحرين', 'Bahrain'],
    'Asia/Muscat': ['عُمان', 'Oman'], 'Asia/Amman': ['الأردن', 'Jordan'], 'Asia/Baghdad': ['العراق', 'Iraq'],
    'Africa/Casablanca': ['المغرب', 'Morocco'], 'Africa/Algiers': ['الجزائر', 'Algeria'], 'Africa/Tunis': ['تونس', 'Tunisia'],
    'Africa/Tripoli': ['ليبيا', 'Libya'], 'Africa/Khartoum': ['السودان', 'Sudan'], 'Asia/Beirut': ['لبنان', 'Lebanon'],
    'Europe/London': ['بريطانيا', 'United Kingdom'], 'Europe/Berlin': ['ألمانيا', 'Germany'], 'Europe/Paris': ['فرنسا', 'France'],
    'America/Toronto': ['كندا', 'Canada'], 'America/Vancouver': ['كندا', 'Canada'], 'America/New_York': ['أمريكا', 'USA'],
    'America/Chicago': ['أمريكا', 'USA'], 'America/Denver': ['أمريكا', 'USA'], 'America/Los_Angeles': ['أمريكا', 'USA'],
    'Australia/Sydney': ['أستراليا', 'Australia'], 'Europe/Istanbul': ['تركيا', 'Turkey'], 'Asia/Kuala_Lumpur': ['ماليزيا', 'Malaysia']
  };
  if (country && !country.value) {
    try { var c = TZ[Intl.DateTimeFormat().resolvedOptions().timeZone]; if (c) country.value = c[en ? 1 : 0]; } catch (e) {}
  }
  form.querySelectorAll('.step-label').forEach(function (p) { p.hidden = false; });
  next.hidden = false; back.hidden = false;
  var step2HasErrors = s2.querySelector('.err') && !s1.querySelector('.err');
  function show(n) { s1.hidden = n !== 1; s2.hidden = n !== 2; (n === 1 ? name : (country || s2.querySelector('input,select'))).focus(); }
  s2.hidden = !(step2HasErrors || (token && token.value));
  s1.hidden = !s2.hidden;
  function err(input, msg) {
    var box = input.parentNode.querySelector('.err.js'); if (box) box.remove();
    if (!msg) return;
    box = document.createElement('div'); box.className = 'err js'; box.textContent = msg; input.parentNode.appendChild(box);
  }
  next.addEventListener('click', function () {
    var ok = true;
    if (!name.value.trim()) { err(name, en ? 'Please write your name' : 'اكتب الاسم'); ok = false; } else err(name);
    if (phone.value.replace(/\D/g, '').length < 7) { err(phone, en ? 'Please write a valid WhatsApp number' : 'اكتب رقم واتساب صحيح'); ok = false; } else err(phone);
    if (!ok) return;
    fillTracking();
    var fd = new FormData(form); if (en) fd.append('lang', 'en');
    fetch(form.getAttribute('data-start-url'), { method: 'POST', body: fd, credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d && d.token && token) token.value = d.token; })
      .catch(function () {});
    if (window.gtag) gtag('event', 'booking_step1', { page: location.pathname });
    show(2);
  });
  back.addEventListener('click', function () { show(1); });
  [name, phone].forEach(function (i) {
    i.addEventListener('keydown', function (e) { if (e.key === 'Enter' && !s1.hidden) { e.preventDefault(); next.click(); } });
  });
  form.addEventListener('submit', fillTracking);
})();
