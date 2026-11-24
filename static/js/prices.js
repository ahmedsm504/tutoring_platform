/* الأسعار بعملة الزائر: بيختار العملة من اختيار الزائر المحفوظ، أو من توقيت الجهاز، وإلا بيسيب العملة اللي جت من السيرفر */
(function () {
  var el = document.getElementById('prices-data');
  if (!el) return;
  var data; try { data = JSON.parse(el.textContent); } catch (e) { return; }
  var lang = (document.documentElement.lang || 'ar').slice(0, 2);
  var selects = document.querySelectorAll('[data-currency-select]');
  var fixed = document.querySelector('[data-currency-fixed]');
  function apply(code) {
    var t = data.tables[code]; if (!t) return;
    document.querySelectorAll('[data-price-table]').forEach(function (tb) {
      tb.querySelectorAll('[data-p]').forEach(function (td) {
        var k = td.getAttribute('data-p').split('-'), row = t.rows[+k[0]];
        if (row) td.textContent = k[1] === '1' ? row[2] : row[1];
      });
      tb.querySelectorAll('[data-dur]').forEach(function (th) {
        var d = t.dur && t.dur[+th.getAttribute('data-dur')];
        if (d) th.textContent = d + (lang === 'en' ? ' min' : ' دقيقة');
      });
      tb.querySelectorAll('[data-price-name]').forEach(function (s) { s.textContent = lang === 'en' ? t.en : t.ar; });
    });
    selects.forEach(function (s) { s.value = code; });
  }
  var code = null;
  try { code = localStorage.getItem('al_currency'); } catch (e) {}
  if (!code && !fixed) {
    try { code = data.tz[Intl.DateTimeFormat().resolvedOptions().timeZone] || null; } catch (e) {}
  }
  if (code && !fixed) apply(code);
  selects.forEach(function (s) {
    s.addEventListener('change', function () {
      try { localStorage.setItem('al_currency', s.value); } catch (e) {}
      apply(s.value);
    });
  });
})();
