/* 辺野古ページ固有の補助表示。集計や投票の正本は変更しない。 */
(function(){
  'use strict';
  function ready(fn){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',fn,{once:true});else fn();}
  ready(function(){
    if(!document.body.classList.contains('henoko-connected'))return;
    var dataNode=document.getElementById('henoko-connected-data'), background=document.getElementById('bukatsu-background');
    if(background&&!background.querySelector('.henoko-status')){
      var status=document.createElement('p');status.className='henoko-status';status.innerHTML='<b>資料確認日</b> <span>'+(dataNode?JSON.parse(dataNode.textContent).background_checked_on:'—')+'</span>　<span>理由別分類は本文を読み直した範囲と未読分を分けて表示</span>';background.insertBefore(status,background.firstChild.nextSibling||background.firstChild);
    }
    var panel=document.getElementById('panel');
    if(panel){
      var observer=new MutationObserver(function(){panel.querySelectorAll('.henoko-sources a').forEach(function(a){a.setAttribute('target','_blank');a.setAttribute('rel','noopener nofollow');});});
      observer.observe(panel,{childList:true,subtree:true});
    }
    var before=function(){document.body.classList.add('henoko-printing');};
    var after=function(){document.body.classList.remove('henoko-printing');};
    window.addEventListener('beforeprint',before);window.addEventListener('afterprint',after);
  });
})();
