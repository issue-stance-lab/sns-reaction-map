/* Presentation only: no data writes, no changes to existing vote/read-progress keys. */
(() => {
  const paths={book:'M3 4h7l2 2 2-2h7v15h-7l-2 2-2-2H3z M12 6v15',chat:'M3 4h18v13H8l-5 4z M7 9h1m3 0h1m3 0h1',chart:'M4 3v18h18 M7 15l4-5 4 3 5-8',search:'M17 17l5 5 M19 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0'};
  function icon(kind){const s=document.createElementNS('http://www.w3.org/2000/svg','svg');s.setAttribute('viewBox','0 0 24 24');s.setAttribute('aria-hidden','true');s.classList.add('renew-picto');const p=document.createElementNS(s.namespaceURI,'path');p.setAttribute('d',paths[kind]);s.append(p);return s;}
  const nav=document.querySelector('.modern-nav'), header=document.querySelector('.modern-header-inner');
  if(nav&&header&&!header.querySelector('.renew-menu')){const d=document.createElement('details');d.className='renew-menu';const summary=document.createElement('summary');summary.textContent='メニュー';d.append(summary,nav.cloneNode(true));d.querySelector('nav').className='';header.append(d);}
  const title=document.querySelector('.hero h1');
  if(title){const text=title.textContent;const chunks=text.match(/[^？?・]+[？?・]?/g)||[text];title.textContent='';chunks.forEach(t=>{const span=document.createElement('span');span.className='phrase';span.textContent=t;title.append(span);});}
  document.querySelectorAll('main>.panel>.panel-title h2,main>.update-dashboard>h2,#planet-block>.panel-title h2').forEach(h=>{if(h.querySelector('svg'))return;const t=h.textContent;h.prepend(icon(/推移|変化|潮目/.test(t)?'chart':/資料|背景|制度/.test(t)?'book':/意見|反応|論点/.test(t)?'chat':'search'));});
})();
