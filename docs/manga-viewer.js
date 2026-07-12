/* manga-viewer.js — shared manga viewer for all themes */
(function(global) {
  function injectCSS() {
    if (document.getElementById('manga-viewer-css')) return;
    var s = document.createElement('style');
    s.id = 'manga-viewer-css';
    s.textContent =
      '.manga-chars{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:20px}' +
      '@media(max-width:600px){.manga-chars{grid-template-columns:1fr}}' +
      '.manga-char-card{display:flex;gap:12px;align-items:center;background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:8px;padding:12px;box-shadow:0 2px 8px rgba(16,24,40,.06)}' +
      '.manga-char-img{width:60px;height:60px;object-fit:cover;border-radius:50%;flex-shrink:0;background:#f0f0f0}' +
      '.manga-char-info{min-width:0}' +
      '.manga-char-name{margin:0 0 2px;font-size:13px;font-weight:900;line-height:1.3}' +
      '.manga-char-role{font-size:11px;color:var(--muted,#888);font-weight:400}' +
      '.manga-char-quote{margin:4px 0 0;font-size:12px;color:var(--ink,#1a1a2e);line-height:1.5;font-style:italic}' +
      '.manga-modal-header{position:absolute;top:0;left:0;right:0;display:flex;align-items:center;padding:12px 64px 10px 16px;background:linear-gradient(rgba(15,23,42,.65),transparent);pointer-events:none;z-index:2}' +
      '.manga-modal-close{pointer-events:all;position:absolute;top:14px;right:16px;z-index:3;border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.12);color:#fff;border-radius:8px;min-width:44px;height:44px;cursor:pointer;font-size:24px;line-height:1;font-weight:900;backdrop-filter:blur(6px)}' +
      '.manga-modal-counter{font-size:12px;color:rgba(255,255,255,.8);min-width:36px;flex-shrink:0}' +
      '.manga-modal-title{font-size:13px;font-weight:900;color:#fff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding-right:8px}' +
      '.manga-modal-prev,.manga-modal-next{position:absolute;border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.12);color:#fff;border-radius:8px;min-width:44px;height:44px;cursor:pointer;font-size:28px;line-height:1;font-weight:900;backdrop-filter:blur(6px);top:50%;transform:translateY(-50%);z-index:2}' +
      '.manga-modal-prev{left:14px}.manga-modal-next{right:14px}' +
      '#manga-modal-image{max-width:min(88vw,820px);max-height:82vh;border-radius:8px;box-shadow:0 24px 80px rgba(0,0,0,.45);background:#fff;transition:transform .08s linear;will-change:transform;user-select:none;-webkit-user-drag:none;display:block}' +
      '.manga-modal-dots{position:absolute;bottom:10px;left:0;right:0;display:flex;justify-content:center;gap:8px;z-index:2;pointer-events:none}' +
      '.manga-modal-dots span{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,.28);transition:background .2s;display:inline-block}' +
      '.manga-modal-dots span.active{background:#fff}' +
      '.manga-modal-dots .dot-end{background:rgba(255,210,80,.25)}' +
      '.manga-modal-dots .dot-end.active{background:rgba(255,210,80,.9)}' +
      '.manga-modal-end{display:none;flex-direction:column;align-items:center;justify-content:center;padding:28px 24px;background:#fff;border-radius:12px;text-align:center;max-width:340px;width:90vw;position:static}' +
      '.manga-modal-end.active{display:flex}' +
      '.manga-modal-end h3{margin:0 0 6px;font-size:16px;color:#1a1a2e;font-weight:900}' +
      '.manga-modal-end p{margin:0 0 16px;font-size:13px;color:#555;line-height:1.6}' +
      '.manga-vote-btn{border:none;background:#1a1a2e;color:#fff;border-radius:8px;padding:11px 24px;cursor:pointer;font-size:14px;font-weight:900;transition:background .18s;position:static}' +
      '.manga-vote-btn:hover{background:#2d2d4e}' +
      '.manga-modal button.manga-vote-btn{position:static;border:none;background:#1a1a2e;color:#fff;min-width:unset;height:auto;font-size:14px;backdrop-filter:none}' +
      '@keyframes mgFadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}' +
      '.manga-page-card.mv-anim{opacity:0}.manga-page-card.mv-anim.mv-visible{animation:mgFadeUp .4s ease forwards}';
    document.head.appendChild(s);
  }

  function mk(tag, cls) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    return e;
  }

  function init(cfg) {
    injectCSS();
    var sectionId = cfg.sectionId || 'manga-section';
    var modalId   = cfg.modalId   || 'manga-modal';
    var voteId    = cfg.voteId    || 'vote-section';
    var endTitle  = cfg.endTitle  || '読んでみて、どう感じた？';
    var endBody   = cfg.endBody   || '二人の言い分、どちらに近い？';
    var endCta    = cfg.endCta    || '投票へ進む';

    var section = document.getElementById(sectionId);
    var modal   = document.getElementById(modalId);
    if (!section || !modal) return;

    /* ── キャラクターカード ── */
    if (cfg.chars && cfg.chars.length) {
      var charsDiv = mk('div', 'manga-chars');
      cfg.chars.forEach(function(c) {
        var card = mk('div', 'manga-char-card');
        var img  = mk('img', 'manga-char-img');
        img.src = c.img; img.alt = c.name; img.loading = 'lazy';
        var info = mk('div', 'manga-char-info');
        var name = mk('p', 'manga-char-name');
        name.innerHTML = c.name + (c.role ? '<br><span class="manga-char-role">' + c.role + '</span>' : '');
        var quote = mk('p', 'manga-char-quote');
        quote.textContent = '「' + c.quote + '」';
        info.appendChild(name);
        info.appendChild(quote);
        card.appendChild(img);
        card.appendChild(info);
        charsDiv.appendChild(card);
      });
      var grid = section.querySelector('.manga-grid');
      if (grid) section.insertBefore(charsDiv, grid);
    }

    /* ── モーダル DOM を再構築 ── */
    modal.innerHTML = '';

    var header  = mk('div', 'manga-modal-header');
    var counter = mk('span', 'manga-modal-counter');
    var titleEl = mk('span', 'manga-modal-title');
    header.appendChild(counter);
    header.appendChild(titleEl);
    modal.appendChild(header);

    var closeBtn = mk('button', 'manga-modal-close');
    closeBtn.type = 'button'; closeBtn.setAttribute('aria-label', '閉じる');
    closeBtn.innerHTML = '&times;';
    modal.appendChild(closeBtn);

    var prevBtn = mk('button', 'manga-modal-prev');
    prevBtn.type = 'button'; prevBtn.setAttribute('aria-label', '前のページ');
    prevBtn.innerHTML = '&#8249;';
    modal.appendChild(prevBtn);

    var mainImg = mk('img', '');
    mainImg.id = 'manga-modal-image';
    modal.appendChild(mainImg);

    var nextBtn = mk('button', 'manga-modal-next');
    nextBtn.type = 'button'; nextBtn.setAttribute('aria-label', '次のページ');
    nextBtn.innerHTML = '&#8250;';
    modal.appendChild(nextBtn);

    var dotsEl = mk('div', 'manga-modal-dots');
    modal.appendChild(dotsEl);

    var endCard = mk('div', 'manga-modal-end');
    var endH3 = mk('h3'); endH3.textContent = endTitle;
    var endP  = mk('p');  endP.textContent  = endBody;
    var voteBtn = mk('button', 'manga-vote-btn');
    voteBtn.type = 'button'; voteBtn.textContent = endCta;
    endCard.appendChild(endH3);
    endCard.appendChild(endP);
    endCard.appendChild(voteBtn);
    modal.appendChild(endCard);

    /* ── ページデータを DOM から収集 ── */
    var cards = [].slice.call(section.querySelectorAll('.manga-page-card'));
    var pages = cards.map(function(card) {
      var im = card.querySelector('img');
      var sp = card.querySelector('span');
      var title = sp ? sp.textContent.replace(/^Page\s*\d+\s*\/\s*\d+\s*/, '').trim() : '';
      return { src: im ? im.getAttribute('src') : '', alt: im ? (im.getAttribute('alt') || '') : '', title: title };
    });

    /* ── ドット生成 ── */
    pages.forEach(function() { dotsEl.appendChild(mk('span', '')); });
    dotsEl.appendChild(mk('span', 'dot-end'));

    function setDots(i) {
      var dots = dotsEl.querySelectorAll('span');
      for (var d = 0; d < dots.length; d++) dots[d].classList.toggle('active', d === i);
    }

    /* ── 状態 ── */
    var idx = 0, isEnd = false;
    var zoomLevel = 1, panX = 0, panY = 0;
    var isDragging = false, dragStart = {x:0, y:0};
    var lastTap = 0;
    var touchStartX = 0, touchStartY = 0, touchDist0 = 0, isZooming = false;

    function resetZoom() { zoomLevel = 1; panX = 0; panY = 0; applyTransform(); }
    function applyTransform() {
      mainImg.style.transform = 'scale(' + zoomLevel + ') translate(' + (panX/zoomLevel) + 'px,' + (panY/zoomLevel) + 'px)';
      mainImg.style.cursor = zoomLevel > 1 ? 'grab' : 'default';
    }

    function showPage(i) {
      if (i < 0) i = 0;
      if (i >= pages.length) { showEnd(); return; }
      isEnd = false; idx = i;
      mainImg.src = pages[i].src; mainImg.alt = pages[i].alt;
      mainImg.style.display = '';
      endCard.classList.remove('active');
      counter.textContent = (i + 1) + ' / ' + pages.length;
      titleEl.textContent = pages[i].title;
      prevBtn.style.display = i === 0 ? 'none' : '';
      nextBtn.style.display = '';
      setDots(i);
      resetZoom();
    }

    function showEnd() {
      isEnd = true;
      mainImg.style.display = 'none';
      endCard.classList.add('active');
      counter.textContent = ''; titleEl.textContent = '';
      prevBtn.style.display = '';
      nextBtn.style.display = 'none';
      setDots(pages.length);
    }

    function openModal(i) {
      modal.classList.add('active');
      modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      showPage(i);
    }

    function closeModal() {
      modal.classList.remove('active');
      modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
      resetZoom();
    }

    /* ── イベント ── */
    cards.forEach(function(card) {
      card.addEventListener('click', function() {
        openModal(parseInt(card.getAttribute('data-manga-index'), 10));
      });
    });

    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', function(e) { if (e.target === modal) closeModal(); });

    prevBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      if (isEnd) { showPage(pages.length - 1); return; }
      if (idx > 0) showPage(idx - 1);
    });
    nextBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      if (!isEnd) showPage(idx + 1);
    });

    voteBtn.addEventListener('click', function() {
      closeModal();
      var target = document.getElementById(voteId);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    document.addEventListener('keydown', function(e) {
      if (!modal.classList.contains('active')) return;
      if (e.key === 'Escape') { closeModal(); return; }
      if (e.key === 'ArrowLeft')  { if (isEnd) showPage(pages.length - 1); else if (idx > 0) showPage(idx - 1); }
      if (e.key === 'ArrowRight') { if (!isEnd) showPage(idx + 1); }
    });

    /* ── ダブルクリック / ダブルタップ zoom ── */
    mainImg.addEventListener('dblclick', function(e) {
      e.preventDefault();
      if (zoomLevel > 1) { resetZoom(); return; }
      zoomLevel = 2;
      var r = mainImg.getBoundingClientRect();
      panX = -(e.clientX - r.left - r.width  / 2);
      panY = -(e.clientY - r.top  - r.height / 2);
      applyTransform();
    });

    /* ── マウスドラッグ（ズーム時）── */
    mainImg.addEventListener('mousedown', function(e) {
      if (zoomLevel <= 1) return;
      isDragging = true;
      dragStart = { x: e.clientX - panX, y: e.clientY - panY };
      mainImg.style.cursor = 'grabbing';
      e.preventDefault();
    });
    document.addEventListener('mousemove', function(e) {
      if (!isDragging) return;
      panX = e.clientX - dragStart.x;
      panY = e.clientY - dragStart.y;
      applyTransform();
    });
    document.addEventListener('mouseup', function() {
      if (isDragging) { isDragging = false; mainImg.style.cursor = zoomLevel > 1 ? 'grab' : 'default'; }
    });

    /* ── タッチ: スワイプ / ピンチ / ダブルタップ ── */
    modal.addEventListener('touchstart', function(e) {
      if (e.touches.length === 2) {
        isZooming = true;
        touchDist0 = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        return;
      }
      isZooming = false;
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
      var now = Date.now();
      if (now - lastTap < 280) {
        if (zoomLevel > 1) { resetZoom(); } else { zoomLevel = 2; applyTransform(); }
        lastTap = 0;
      } else {
        lastTap = now;
      }
    }, { passive: true });

    modal.addEventListener('touchmove', function(e) {
      if (e.touches.length === 2 && isZooming) {
        var d = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        zoomLevel = Math.min(4, Math.max(1, zoomLevel * d / touchDist0));
        touchDist0 = d;
        applyTransform();
        if (zoomLevel > 1) e.preventDefault();
        return;
      }
      if (e.touches.length === 1 && zoomLevel > 1) {
        panX += e.touches[0].clientX - touchStartX;
        panY += e.touches[0].clientY - touchStartY;
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        applyTransform();
        e.preventDefault();
      }
    }, { passive: false });

    modal.addEventListener('touchend', function(e) {
      if (isZooming) { isZooming = false; return; }
      if (zoomLevel > 1) return;
      var dx = e.changedTouches[0].clientX - touchStartX;
      var dy = e.changedTouches[0].clientY - touchStartY;
      if (Math.abs(dx) > 44 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        if (dx < 0) { if (!isEnd) showPage(idx + 1); }
        else { if (isEnd) showPage(pages.length - 1); else if (idx > 0) showPage(idx - 1); }
      }
    }, { passive: true });

    /* ── スクロールフェードイン ── */
    if ('IntersectionObserver' in window) {
      cards.forEach(function(card, i) {
        card.classList.add('mv-anim');
        card.style.animationDelay = (i * 0.1) + 's';
        var obs = new IntersectionObserver(function(entries) {
          if (entries[0].isIntersecting) { card.classList.add('mv-visible'); obs.disconnect(); }
        }, { threshold: 0.15 });
        obs.observe(card);
      });
    }
  }

  global.MangaViewer = { init: init };
})(window);
