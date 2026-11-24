/* مصدر الزائر لفورم الحجز (accounts/tracking.py): كوكي أول دخول (أول صفحة + الموقع اللي جه منه + UTM)
   وكوكي آخر صفحة قبل الحجز. كوكيز طرف أول بس، من غير أي بيانات شخصية. */
(function () {
  function get(n) { var m = document.cookie.match('(?:^|; )' + n + '=([^;]*)'); return m ? decodeURIComponent(m[1]) : ''; }
  function set(n, v, days) {
    var e = days ? '; max-age=' + days * 86400 : '';
    document.cookie = n + '=' + encodeURIComponent(v) + e + '; path=/; SameSite=Lax' + (location.protocol === 'https:' ? '; Secure' : '');
  }
  var path = location.pathname, q = new URLSearchParams(location.search);
  var utm = ['utm_source', 'utm_medium', 'utm_campaign'].map(function (k) { return q.get(k) || ''; });
  var hasUtm = utm.join('') !== '';
  var click = q.get('gclid') ? 'gclid' : (q.get('fbclid') ? 'fbclid' : '');
  var ref = document.referrer && document.referrer.indexOf(location.host) === -1 ? document.referrer : '';
  // أول دخول، أو دخول جديد من حملة/إعلان (بيغلب لأنه أوضح مصدر)
  if (!get('al_first') || hasUtm || click) {
    set('al_first', JSON.stringify({ l: path, r: ref.slice(0, 250), u: hasUtm ? utm.join('|') : '', c: click }), 90);
  }
  var isContact = /\/contact\/?$/.test(path);
  if (!isContact && !/thank-you/.test(path)) set('al_prev', path, 0);
  if (isContact) {
    document.querySelectorAll('form[data-booking]').forEach(function (f) {
      var a = f.querySelector('[name=trk_first]'), b = f.querySelector('[name=trk_prev]');
      if (a) a.value = get('al_first');
      if (b) b.value = get('al_prev');
    });
  }
})();
