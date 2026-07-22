(function(){
  var ogTitle=(document.querySelector('meta[property="og:title"]')||{}).content||document.title;
  var ogUrl=(document.querySelector('meta[property="og:url"]')||{}).content||location.href;

  var style=document.createElement('style');
  style.textContent=[
    '.share-x-fab{position:fixed;bottom:20px;right:20px;z-index:9990;display:inline-flex;align-items:center;gap:8px;padding:12px 20px;border-radius:999px;border:0;background:#000;color:#fff;font-family:inherit;font-size:14px;font-weight:900;cursor:pointer;box-shadow:0 6px 24px rgba(0,0,0,.28);transition:transform .15s,box-shadow .15s;text-decoration:none;line-height:1}',
    '.share-x-fab:hover{transform:translateY(-2px);box-shadow:0 10px 32px rgba(0,0,0,.36)}',
    '.share-x-fab svg{flex-shrink:0}',
    '@media(max-width:480px){.share-x-fab span{display:none}.share-x-fab{padding:14px}}'
  ].join('');
  document.head.appendChild(style);

  var text=ogTitle+'\n#SNS反応まっぷ';
  var href='https://x.com/intent/tweet?text='+encodeURIComponent(text)+'&url='+encodeURIComponent(ogUrl);

  var btn=document.createElement('a');
  btn.className='share-x-fab';
  btn.href=href;
  btn.target='_blank';
  btn.rel='noopener';
  btn.setAttribute('aria-label','Xでポスト');
  btn.innerHTML='<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg><span>Xでポスト</span>';
  document.body.appendChild(btn);
})();
