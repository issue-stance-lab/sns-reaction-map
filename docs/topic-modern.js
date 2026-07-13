(function () {
  var header = document.querySelector('.modern-site-header');
  if (!header) {
    document.body.insertAdjacentHTML('afterbegin',
      '<header class="modern-site-header">' +
        '<div class="modern-header-inner">' +
          '<a class="modern-logo" href="index.html" aria-label="SNS反応まっぷ トップ">' +
            '<span class="modern-logo-mark" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></span>' +
            '<span class="modern-logo-text">SNS反応まっぷ</span>' +
          '</a>' +
          '<nav class="modern-nav" aria-label="メインナビゲーション">' +
            '<a href="index.html#topics">テーマ一覧</a>' +
            '<a href="index.html#ranking">ランキング</a>' +
            '<a href="about.html">データについて</a>' +
            '<a href="usage.html">使い方</a>' +
            '<a href="usage.html#faq">よくある質問</a>' +
          '</nav>' +
          '<a class="modern-header-button" href="index.html#topics">テーマを見る</a>' +
        '</div>' +
      '</header>');
  }

  var title = document.querySelector('.hero h1');
  if (title) {
    title.textContent = title.textContent.replace(/\s*SNS反応まっぷ\s*$/, '');
    var breadcrumb = document.querySelector('.hero .top-nav a');
    if (breadcrumb) breadcrumb.setAttribute('data-topic-title', title.textContent.trim());
  }
})();
