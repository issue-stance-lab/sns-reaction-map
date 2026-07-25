(function () {
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
    share.href = 'https://x.com/intent/tweet?text=' + encodeURIComponent(shareText) +
      '&url=' + encodeURIComponent(location.href.split('#')[0]);

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

  function getPrimaryArena() {
    return document.getElementById('issue-arena-section') ||
      document.getElementById('stance-map-section');
  }

  function getArenaContent(section) {
    if (!section) return null;
    var inner = section.querySelector('#issue-arena-inner, #stance-map-inner, .arena-gated-content');
    if (inner) return inner;

    inner = document.createElement('div');
    inner.id = 'issue-arena-inner';
    inner.className = 'arena-gated-content';
    while (section.firstChild) inner.appendChild(section.firstChild);
    section.appendChild(inner);
    return inner;
  }

  function normalizeArenaLayout(section, inner) {
    if (!section || !inner) return null;
    var title = inner.querySelector(':scope > .panel-title');
    var caption = inner.querySelector(':scope > .map-caption, :scope > .map-caption-a, :scope > .arena-caption');
    var board = inner.querySelector(':scope > #sm-wrap, :scope > #sm-wrap-arena, :scope > #arena-wrap, :scope > .arena-wrap');
    var note = inner.querySelector(':scope > #your-marker-note-arena, :scope > #your-marker-note, :scope > #arena-marker-note, :scope > .arena-user-note');
    var controls = inner.querySelector(':scope > .sm-controls, :scope > .arena-controls, :scope > .arena-legend');
    var tooltip = inner.querySelector(':scope > #sm-tooltip, :scope > #sm-tooltip-arena, :scope > .arena-tooltip');

    [title, caption, board, note, controls, tooltip].forEach(function (element) {
      if (element) inner.appendChild(element);
    });
    return board || inner.querySelector('canvas');
  }

  function positionArenaOverlay(overlay, section, board) {
    if (!overlay || !section || !board) return;
    var sectionRect = section.getBoundingClientRect();
    var boardRect = board.getBoundingClientRect();
    overlay.style.inset = 'auto';
    overlay.style.top = (boardRect.top - sectionRect.top) + 'px';
    overlay.style.left = (boardRect.left - sectionRect.left) + 'px';
    overlay.style.width = boardRect.width + 'px';
    overlay.style.height = boardRect.height + 'px';
  }

  function lockArenaUntilVote() {
    var section = getPrimaryArena();
    var inner = getArenaContent(section);
    if (!section || !inner) return;
    var board = normalizeArenaLayout(section, inner);

    inner.style.filter = 'blur(8px)';
    inner.style.pointerEvents = 'none';
    inner.style.userSelect = 'none';
    inner.setAttribute('aria-hidden', 'true');
    section.classList.add('arena-is-locked');

    section.querySelectorAll('#arena-overlay, #chart-overlay, #topic-arena-overlay').forEach(function (oldOverlay) {
      oldOverlay.remove();
    });
    var overlay = document.createElement('div');
    overlay.id = 'topic-arena-overlay';
    overlay.className = 'topic-arena-overlay';
    overlay.innerHTML =
      '<div class="topic-arena-overlay-card">' +
        '<strong>まず投票してからアリーナを見よう</strong>' +
        '<span>上の投票で論点と考えを選んでください</span>' +
      '</div>';
    section.appendChild(overlay);
    positionArenaOverlay(overlay, section, board);
  }

  function revealArenaAfterVote() {
    var section = getPrimaryArena();
    var inner = getArenaContent(section);
    if (!section || !inner) return;

    inner.style.transition = 'filter .45s ease';
    inner.style.filter = 'none';
    inner.style.pointerEvents = 'auto';
    inner.style.userSelect = 'auto';
    inner.removeAttribute('aria-hidden');
    section.classList.remove('arena-is-locked');
    section.querySelectorAll('#arena-overlay, #chart-overlay, #topic-arena-overlay').forEach(function (overlay) {
      overlay.remove();
    });
  }

  window.lockArenaUntilVote = lockArenaUntilVote;
  window.revealArenaAfterVote = revealArenaAfterVote;

  lockArenaUntilVote();
  window.addEventListener('resize', function () {
    var section = getPrimaryArena();
    var inner = getArenaContent(section);
    var overlay = section && section.querySelector('#topic-arena-overlay');
    var board = normalizeArenaLayout(section, inner);
    positionArenaOverlay(overlay, section, board);
  });

  [
    'setArenaVoteMarker',
    'setStanceMapVoteMarker',
    'setConstitutionalVoteMarker',
    'setHenokoArenaMarker',
    'setNicknameArenaMarker',
    'setTakaichiArenaMarker'
  ].forEach(function (name) {
    var original = window[name];
    if (typeof original !== 'function' || original.__arenaGateWrapped) return;
    var wrapped = function () {
      var result = original.apply(this, arguments);
      revealArenaAfterVote();
      return result;
    };
    wrapped.__arenaGateWrapped = true;
    window[name] = wrapped;
  });

  [
    'clearArenaVoteMarker',
    'clearStanceMapVoteMarker',
    'clearConstitutionalVoteMarker',
    'clearHenokoArenaMarker',
    'clearNicknameArenaMarker',
    'clearTakaichiArenaMarker'
  ].forEach(function (name) {
    var original = window[name];
    if (typeof original !== 'function' || original.__arenaGateWrapped) return;
    var wrapped = function () {
      var result = original.apply(this, arguments);
      lockArenaUntilVote();
      return result;
    };
    wrapped.__arenaGateWrapped = true;
    window[name] = wrapped;
  });

  var visibleMarkerNote = document.querySelector(
    '#your-marker-note-arena:not([style*="display:none"]), ' +
    '#your-marker-note:not([style*="display:none"]), ' +
    '#arena-marker-note:not([style*="display:none"])'
  );
  if (visibleMarkerNote && getComputedStyle(visibleMarkerNote).display !== 'none') {
    revealArenaAfterVote();
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

})();
