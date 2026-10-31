/* 課題51: 記事の案内クリックと、移動先の理由一覧が表示された利用者を別々に数える。
   GA4の既存イベントは残す。利用者の重複はGA4のtotalUsersで集計する。 */
(function () {
  'use strict';
  if (location.hostname !== 'sns-reaction-map.jp') return;

  function parseUrl(value) {
    try { return new URL(value, location.href); } catch (_) { return null; }
  }
  function isTest(url) { return url && url.searchParams.get('analytics_test') === '1'; }
  var current = parseUrl(location.href);
  var referrer = document.referrer ? parseUrl(document.referrer) : null;
  if (isTest(current) || isTest(referrer)) return;
  function send(name, params) {
    if (typeof window.gtag !== 'function') return false;
    window.gtag('event', name, params);
    return true;
  }

  var article = document.body && document.body.getAttribute('data-article');
  if (article && article !== 'index') {
    document.addEventListener('click', function (event) {
      var a = event.target.closest && event.target.closest('a[href]');
      var target = a && parseUrl(a.href);
      if (!target || target.origin !== location.origin
          || !/^\/[a-z0-9-]+-reaction-map\.html$/.test(target.pathname)
          || !/^#issue-[a-z0-9_-]+$/.test(target.hash)) return;
      send('article_reason_click', {
        article: article, issue_id: target.hash.slice(7),
        link_url: target.origin + target.pathname + target.hash
      });
    });
    return;
  }

  // 同一サイトの記事から直接来たページだけ。保存やユーザー識別子は追加しない。
  var source = referrer && referrer.origin === location.origin
    && /^\/articles\/([a-z0-9-]+)\.html$/.exec(referrer.pathname);
  if (!source || source[1] === 'index' || !window.IntersectionObserver) return;
  var sent = false;
  var visible = new Set();
  var observer;
  function record() {
    if (sent || document.visibilityState !== 'visible') return;
    visible.forEach(function (row) {
      if (sent) return;
      var panel = row.closest('[data-issue-panel]');
      if (!panel || !panel.hasAttribute('data-selected')) return;
      if (send('article_reason_view', {
        article: source[1], issue_id: panel.getAttribute('data-issue-panel'),
        page_referrer: referrer.origin + referrer.pathname
      })) {
        sent = true;
        observer.disconnect();
      }
    });
  }
  observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting && entry.intersectionRatio >= 0.5) visible.add(entry.target);
      else visible.delete(entry.target);
    });
    record();
  }, { threshold: [0, 0.5] });
  // 長いパネル全体や見出しではなく、理由一覧の先頭行の半分以上が見えたとき。
  document.querySelectorAll('[data-issue-panel]').forEach(function (panel) {
    var row = panel.querySelector('.fr-reason-pick');
    if (row) observer.observe(row);
  });
  document.addEventListener('visibilitychange', record);
})();
