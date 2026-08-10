(function () {
  // ---- 共有URLの正典 ------------------------------------------------------
  // シェア導線（FAB / 投票後 / ビルダー生成分）は必ずここを通す。
  // UTMが無いとGA4では t.co / referral にまとまり、どの導線からの流入か区別できない。
  // GROWTH.yaml で share_button 経由の流入がゼロのままなのは施策の失敗ではなく、
  // どのボタンも一度もUTMを付けていなかったため（2026-08-10 判明）。
  window.SHARE_UTM_SOURCE = 'share_button';

  window.buildShareUrl = function (baseUrl, campaign) {
    try {
      var url = new URL(baseUrl || location.href, location.href);
      url.hash = '';
      url.searchParams.set('utm_source', window.SHARE_UTM_SOURCE);
      url.searchParams.set('utm_medium', 'social');
      url.searchParams.set('utm_campaign', campaign);
      return url.toString();
    } catch (e) {
      return baseUrl || location.href;
    }
  };

  // クリック自体もGA4へ送る。UTMだけでは「押されていない」と
  // 「押されたが流入しなかった」を区別できない（Xの投稿画面は別サイトのため）。
  window.trackShareClick = function (campaign) {
    if (typeof window.gtag === 'function') {
      window.gtag('event', campaign + '_click', { utm_campaign: campaign });
    }
  };

  // ---- 関連テーマのクリック計測（未実装ページの受け皿）--------------------
  // 8ページはページ内のインラインJSが計測しているが、fukushuto / koshitsu-tenpakai /
  // takaichi の3ページには計測が無く、関連テーマ枠は出ているのにクリックが
  // 記録されていなかった（2026-08-10 判明）。注目テーマ fukushuto を含むため、
  // GROWTH.yaml の related-themes-block を判定できない一因になっていた。
  function topicSlugFrom(fileName) {
    return (fileName || '').replace(/-reaction-map(-standard)?\.html$|\.html$/, '');
  }

  function bindRelatedThemeFallback() {
    var cards = document.querySelectorAll('a.related-card');
    if (!cards.length) return;
    // 既存のインライン計測があるページでは二重に送らない。
    // そちらは data-related-target を後付けしてから委譲リスナで拾う実装。
    if (document.querySelector('a.related-card[data-related-target]')) return;
    var source = topicSlugFrom(location.pathname.split('/').pop()) || 'unknown';
    Array.prototype.forEach.call(cards, function (card) {
      card.addEventListener('click', function () {
        if (typeof window.gtag !== 'function') return;
        window.gtag('event', 'related_theme_click', {
          source_topic: source,
          target_topic: topicSlugFrom((card.getAttribute('href') || '').split('/').pop()),
          placement: 'page_bottom'
        });
      });
    });
  }

  // インライン側の DOMContentLoaded 処理より後に判定するため1テンポ遅らせる
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      setTimeout(bindRelatedThemeFallback, 0);
    });
  } else {
    setTimeout(bindRelatedThemeFallback, 0);
  }

  window.drawArenaUserMarker = function (ctx, options) {
    if (!ctx || !options) return;
    var x = options.x;
    var y = options.y;
    var color = options.color || '#7c3aed';
    var canvasSize = options.canvasSize || (ctx.canvas && ctx.canvas.width) || 640;
    var label = 'あなたはここ';
    var pulse = (Date.now() % 1400) / 1400;

    ctx.save();
    ctx.beginPath();
    ctx.arc(x, y, 10 + pulse * 16, 0, Math.PI * 2);
    ctx.strokeStyle = color;
    ctx.globalAlpha = 0.55 * (1 - pulse);
    ctx.lineWidth = 3;
    ctx.stroke();
    ctx.globalAlpha = 1;

    ctx.beginPath();
    ctx.arc(x, y, 11, 0, Math.PI * 2);
    ctx.fillStyle = '#fff';
    ctx.fill();
    ctx.beginPath();
    ctx.arc(x, y, 8, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();

    ctx.font = 'bold 12px "Noto Sans JP", sans-serif';
    var textWidth = ctx.measureText(label).width;
    var badgeX = Math.max(textWidth / 2 + 10, Math.min(canvasSize - textWidth / 2 - 10, x));
    var badgeY = Math.max(18, y - 32);
    ctx.beginPath();
    if (ctx.roundRect) {
      ctx.roundRect(badgeX - textWidth / 2 - 8, badgeY - 11, textWidth + 16, 22, 11);
    } else {
      ctx.rect(badgeX - textWidth / 2 - 8, badgeY - 11, textWidth + 16, 22);
    }
    ctx.fillStyle = '#fff';
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, badgeX, badgeY + 1);

    ctx.beginPath();
    ctx.moveTo(x - 4, badgeY + 11);
    ctx.lineTo(x, badgeY + 17);
    ctx.lineTo(x + 4, badgeY + 11);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.restore();
  };

  window.drawArenaSectorHighlight = function (ctx, options) {
    if (!ctx || !options) return;
    var cx = options.cx;
    var cy = options.cy;
    var innerRadius = options.innerRadius;
    var outerRadius = options.outerRadius;
    var start = options.startAngle;
    var end = options.endAngle;
    var color = options.color || '#7c3aed';
    if (options.degrees) {
      start = start * Math.PI / 180;
      end = end * Math.PI / 180;
    }

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(cx + innerRadius * Math.cos(start), cy + innerRadius * Math.sin(start));
    ctx.arc(cx, cy, outerRadius, start, end);
    ctx.arc(cx, cy, innerRadius, end, start, true);
    ctx.closePath();
    ctx.fillStyle = color + '30';
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.lineWidth = 4;
    ctx.shadowColor = color;
    ctx.shadowBlur = 10;
    ctx.stroke();
    ctx.restore();
  };

  function normalizeVoteResult() {
    var result = document.getElementById('vote-result');
    if (!result || !result.textContent.trim() || result.dataset.resultNormalizing === 'true') return;
    if (getComputedStyle(result).display === 'none') return;

    var label = result.querySelector('#vote-position-label');
    var description = result.querySelector('#vote-position-text');
    if (!label) {
      label = result.querySelector(':scope > strong');
      if (label) label.id = 'vote-position-label';
    }
    if (!description) {
      description = result.querySelector(':scope > p');
      if (description) description.id = 'vote-position-text';
    }
    if (!label) return;
    result.dataset.resultNormalizing = 'true';

    if (label.textContent.trim() === 'あなたの選択' && description) {
      var match = description.textContent.match(/「(.+?)」を重視し、総合的には「(.+?)」/);
      if (match) label.textContent = '論点：' + match[1] + ' ／ ' + match[2];
    }
    if (description) {
      description.textContent = description.textContent.replace(/undefined/g, '').trim();
    }

    var card = label.parentElement;
    if (card === result) {
      card = document.createElement('div');
      result.insertBefore(card, label);
      card.appendChild(label);
      if (description) card.appendChild(description);
    }
    card.classList.add('vote-result-card');

    var participantSummary = result.querySelector('.participant-vote-summary');
    if (!participantSummary) {
      participantSummary = document.createElement('p');
      participantSummary.className = 'participant-vote-summary';
      result.insertBefore(participantSummary, card);
    }
    participantSummary.textContent = 'このサイトの参加者投票 n=集計中（訪問者の任意回答です）';

    var voteSection = document.getElementById('vote-section');
    var voteTopic = voteSection && voteSection.dataset.voteTopic;
    if (voteTopic && window.VoteStore && result.dataset.participantCountLoading !== 'true' &&
        result.dataset.participantCountLoaded !== 'true') {
      result.dataset.participantCountLoading = 'true';
      VoteStore.getCounts(voteTopic).then(function (response) {
        var counts = response.counts || {};
        var participantTotal = Object.keys(counts).reduce(function (sum, key) {
          return sum + (Number(counts[key]) || 0);
        }, 0);
        if (response.mode === 'local' && participantTotal === 0) participantTotal = 1;
        participantSummary.textContent = 'このサイトの参加者投票 n=' + participantTotal +
          '（訪問者の任意回答です）';
        result.dataset.participantCountLoaded = 'true';
      }).catch(function (error) {
        console.error('Participant vote count failed:', error);
        participantSummary.textContent = 'このサイトの参加者投票 n=取得失敗（訪問者の任意回答です）';
      }).finally(function () {
        delete result.dataset.participantCountLoading;
      });
    }

    var share = result.querySelector('#share-x');
    var redo = result.querySelector('#vote-redo-btn, #vote-redo');
    var actions = (share && share.parentElement !== result && share.parentElement) ||
      (redo && redo.parentElement !== result && redo.parentElement);
    if (!actions || actions === card) {
      actions = document.createElement('div');
      result.appendChild(actions);
    }
    actions.classList.add('vote-result-actions');

    if (!share) {
      share = document.createElement('a');
      share.id = 'share-x';
      share.target = '_blank';
      share.rel = 'noopener';
      actions.appendChild(share);
    } else if (share.parentElement !== actions) {
      actions.appendChild(share);
    }
    share.textContent = '𝕏 でシェア';
    var shareText = label.textContent.trim() + ' #SNS反応まっぷ';
    // 以前は location.href をそのまま渡していたためUTMが付かず、
    // 投票後シェア経由の流入をGA4で識別できなかった
    share.href = 'https://x.com/intent/tweet?text=' + encodeURIComponent(shareText) +
      '&url=' + encodeURIComponent(window.buildShareUrl(location.href, 'vote_share'));
    if (share.dataset.shareTracked !== '1') {
      share.addEventListener('click', function () { window.trackShareClick('vote_share'); });
      share.dataset.shareTracked = '1';
    }

    if (redo) {
      if (redo.parentElement !== actions) actions.appendChild(redo);
      redo.textContent = '投票をやり直す';
    }

    result.classList.add('vote-result-unified');
    setTimeout(function () {
      delete result.dataset.resultNormalizing;
    }, 0);
  }

  var voteResult = document.getElementById('vote-result');
  if (voteResult) {
    new MutationObserver(normalizeVoteResult).observe(voteResult, {
      attributes: true,
      attributeFilter: ['style', 'hidden'],
      childList: true,
      subtree: true
    });
    normalizeVoteResult();
  }

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
            '<a href="index.html#featured-questions">注目の問い</a>' +
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

  var voteStep1 = document.getElementById('vote-step1');
  var voteStep2 = document.getElementById('vote-step2');
  if (voteStep1 && voteStep2 && !voteStep2.querySelector('.vote-step-back')) {
    var step2UsesHidden = voteStep2.hasAttribute('hidden');
    var voteStepLabel = voteStep2.querySelector('.vote-step-label');
    var step2Head = document.createElement('div');
    step2Head.className = 'vote-step2-head';

    if (voteStepLabel) {
      var stepNumber = voteStepLabel.querySelector('.step-num');
      var questionParts = [];
      for (var labelIndex = 0; labelIndex < voteStepLabel.childNodes.length; labelIndex++) {
        var labelNode = voteStepLabel.childNodes[labelIndex];
        if (labelNode.nodeType === 3 && labelNode.textContent.trim()) {
          questionParts.push(labelNode.textContent.trim());
        }
      }

      var questionCopy = document.createElement('span');
      questionCopy.className = 'vote-step2-copy';

      var questionText = document.createElement('span');
      questionText.className = 'vote-step2-question';
      questionText.textContent = questionParts.join(' ');

      var commonHelper = document.createElement('small');
      commonHelper.className = 'vote-step2-helper';
      commonHelper.textContent = '選ぶと結果を表示します';

      questionCopy.appendChild(questionText);
      questionCopy.appendChild(commonHelper);
      voteStepLabel.textContent = '';
      if (stepNumber) voteStepLabel.appendChild(stepNumber);
      voteStepLabel.appendChild(questionCopy);

      voteStep2.insertBefore(step2Head, voteStepLabel);
      step2Head.appendChild(voteStepLabel);
    } else {
      voteStep2.insertBefore(step2Head, voteStep2.firstChild);
    }

    var voteStepBack = document.createElement('button');
    voteStepBack.type = 'button';
    voteStepBack.className = 'vote-step-back';
    voteStepBack.textContent = '← 論点を選び直す';
    voteStepBack.setAttribute('aria-label', '1問目に戻って論点を選び直す');
    step2Head.appendChild(voteStepBack);

    voteStepBack.addEventListener('click', function () {
      if (step2UsesHidden) {
        voteStep2.hidden = true;
      } else {
        voteStep2.style.display = 'none';
      }
      voteStep1.hidden = false;
      voteStep1.style.display = 'block';

      var firstIssue = voteStep1.querySelector('button:not([disabled])');
      if (firstIssue) firstIssue.focus();

      if (window.gtag) {
        window.gtag('event', 'vote_step1_reselect', {
          topic: document.body.getAttribute('data-topic') || document.title
        });
      }
    });
  }

  /* === 投票完了イベントの発火 =====================================
     各テーマページの「次に投票するテーマ」回遊カードは
     document の "vote2d:revealed" を待って描画されるが、
     このイベントを発火する実装がどのページにも無く、
     6ページで回遊カードが表示されないままになっていた。
     投票結果（#vote-result）が可視になったら、ここで一度だけ発火する。
  ================================================================ */
  var voteResult = document.getElementById('vote-result');
  if (voteResult) {
    var voteRevealed = false;
    var announceVoteReveal = function () {
      if (voteRevealed) return;
      var visible = voteResult.offsetParent !== null || getComputedStyle(voteResult).display !== 'none';
      if (!visible) return;
      voteRevealed = true;
      document.dispatchEvent(new CustomEvent('vote2d:revealed'));
    };
    new MutationObserver(announceVoteReveal).observe(voteResult, {
      attributes: true,
      attributeFilter: ['style', 'class', 'hidden']
    });
    // 過去の投票が localStorage から復元されて最初から表示されている場合
    document.addEventListener('DOMContentLoaded', announceVoteReveal);
    announceVoteReveal();
  }

  /* === 論点図解の拡大ビューア =====================================
     ほとんどのテーマページは開閉をインラインスクリプトで持っているので、
     ここでは開いたあとの「拡大・パン」を足す。
     モーダル自体を持たないページ（辺野古など）では要素と開閉も用意する。
     21:9の論点図解はモバイルで画面幅に収めると文字が読めないため、
     タップで原寸相当まで拡大し、スクロールでパンできるようにする。
     ピンチズームはCSSの touch-action で端末側の機能に任せる。
  ================================================================ */
  var explainerCards = document.querySelectorAll('.explainer-card[data-img]');
  var explainerModal = document.getElementById('explainer-modal');
  var explainerImg = explainerModal && explainerModal.querySelector('#explainer-modal-img');
  var modalWasCreated = false;

  if (explainerCards.length && !explainerModal) {
    explainerModal = document.createElement('div');
    explainerModal.className = 'explainer-modal';
    explainerModal.id = 'explainer-modal';
    explainerModal.setAttribute('role', 'dialog');
    explainerModal.setAttribute('aria-modal', 'true');
    explainerModal.innerHTML =
      '<button class="explainer-modal-close" id="explainer-modal-close" aria-label="閉じる">×</button>' +
      '<img src="" alt="" id="explainer-modal-img">';
    document.body.appendChild(explainerModal);
    explainerImg = explainerModal.querySelector('#explainer-modal-img');
    modalWasCreated = true;
  }

  if (explainerModal && explainerImg) {
    // ページ側に開閉スクリプトが無い場合だけ、ここで開閉も担当する
    if (modalWasCreated) {
      var closeButton = explainerModal.querySelector('.explainer-modal-close');
      var closeModal = function () { explainerModal.classList.remove('open'); };
      Array.prototype.forEach.call(explainerCards, function (card) {
        var open = function () {
          explainerImg.src = card.getAttribute('data-img');
          explainerImg.alt = card.getAttribute('data-alt') || '';
          explainerModal.classList.add('open');
        };
        card.addEventListener('click', open);
        card.addEventListener('keydown', function (event) {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            open();
          }
        });
      });
      closeButton.addEventListener('click', closeModal);
      explainerModal.addEventListener('click', function (event) {
        if (event.target === explainerModal) closeModal();
      });
      document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') closeModal();
      });
    }

    var ZOOM_MAX_WIDTH = 2400;
    var hint = explainerModal.querySelector('.explainer-modal-hint');
    if (!hint) {
      hint = document.createElement('p');
      hint.className = 'explainer-modal-hint';
      explainerModal.appendChild(hint);
    }

    function fitWidth() {
      return Math.max(explainerModal.clientWidth - 24, 1);
    }

    // 画面に収めた状態より大きく表示できるときだけ拡大操作を出す
    function canZoom() {
      if (!explainerImg.naturalWidth) return false;
      return Math.min(explainerImg.naturalWidth, ZOOM_MAX_WIDTH) > fitWidth() + 40;
    }

    function updateHint() {
      if (!canZoom()) {
        hint.hidden = true;
        return;
      }
      hint.hidden = false;
      hint.textContent = explainerModal.classList.contains('is-zoom')
        ? 'ドラッグまたはスクロールで移動／もう一度タップで戻す'
        : 'タップで拡大';
    }

    function applyZoomState() {
      explainerModal.classList.toggle('is-zoomable', canZoom());
      updateHint();
    }

    // ratioX/ratioY は画像内のどの位置を中心に持っていくか（0〜1）
    function zoomIn(ratioX, ratioY) {
      if (!canZoom()) return;
      var width = Math.min(explainerImg.naturalWidth, ZOOM_MAX_WIDTH);
      explainerModal.classList.add('is-zoom');
      explainerImg.style.width = width + 'px';
      explainerImg.style.maxWidth = 'none';
      // レイアウト確定後にスクロール位置を合わせる
      var rect = explainerImg.getBoundingClientRect();
      explainerModal.scrollLeft = ratioX * rect.width - explainerModal.clientWidth / 2;
      explainerModal.scrollTop = ratioY * rect.height - explainerModal.clientHeight / 2;
      updateHint();
    }

    function zoomOut() {
      explainerModal.classList.remove('is-zoom');
      explainerImg.style.width = '';
      explainerImg.style.maxWidth = '';
      explainerModal.scrollLeft = 0;
      explainerModal.scrollTop = 0;
      updateHint();
    }

    explainerImg.addEventListener('click', function (event) {
      event.stopPropagation();
      if (explainerModal.classList.contains('is-zoom')) {
        zoomOut();
        return;
      }
      var rect = explainerImg.getBoundingClientRect();
      zoomIn(
        (event.clientX - rect.left) / rect.width,
        (event.clientY - rect.top) / rect.height
      );
    });

    // マウスでのドラッグパン（タッチは端末のスクロールに任せる）
    var dragging = false;
    var dragFrom = null;

    explainerImg.addEventListener('pointerdown', function (event) {
      if (event.pointerType === 'touch') return;
      if (!explainerModal.classList.contains('is-zoom')) return;
      dragging = true;
      dragFrom = {
        x: event.clientX,
        y: event.clientY,
        left: explainerModal.scrollLeft,
        top: explainerModal.scrollTop,
        moved: false
      };
      explainerImg.classList.add('is-grabbing');
    });

    window.addEventListener('pointermove', function (event) {
      if (!dragging || !dragFrom) return;
      var dx = event.clientX - dragFrom.x;
      var dy = event.clientY - dragFrom.y;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) dragFrom.moved = true;
      explainerModal.scrollLeft = dragFrom.left - dx;
      explainerModal.scrollTop = dragFrom.top - dy;
      event.preventDefault();
    });

    window.addEventListener('pointerup', function (event) {
      if (!dragging) return;
      dragging = false;
      explainerImg.classList.remove('is-grabbing');
      // ドラッグ後のクリックで縮小してしまわないように打ち消す
      if (dragFrom && dragFrom.moved) {
        explainerImg.addEventListener('click', function stop(e) {
          e.stopImmediatePropagation();
          explainerImg.removeEventListener('click', stop, true);
        }, true);
      }
      dragFrom = null;
    });

    // トラックパッドのピンチ（ctrlKey付きwheel）でも拡大・縮小できるようにする
    explainerModal.addEventListener('wheel', function (event) {
      if (!event.ctrlKey) return;
      event.preventDefault();
      var rect = explainerImg.getBoundingClientRect();
      if (event.deltaY < 0) {
        if (!explainerModal.classList.contains('is-zoom')) {
          zoomIn(
            (event.clientX - rect.left) / rect.width,
            (event.clientY - rect.top) / rect.height
          );
        }
      } else if (explainerModal.classList.contains('is-zoom')) {
        zoomOut();
      }
    }, { passive: false });

    explainerImg.addEventListener('load', applyZoomState);
    window.addEventListener('resize', function () {
      if (explainerModal.classList.contains('open')) applyZoomState();
    });

    // 開閉は各ページ側で class を付け外しするので、それを見て状態を初期化する
    new MutationObserver(function () {
      if (explainerModal.classList.contains('open')) {
        applyZoomState();
      } else if (explainerModal.classList.contains('is-zoom')) {
        zoomOut();
      }
    }).observe(explainerModal, { attributes: true, attributeFilter: ['class'] });

    applyZoomState();
  }

})();
