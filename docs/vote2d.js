/*!
 * vote2d.js — 2D キャンバス投票コンポーネント
 * v4: 開票前クイズ(A) / 近い声・遠い声(B) / ピンバウンス+紙吹雪(F)
 */
(function (w, d) {
  'use strict';

  /* ---------- 定数 ---------- */
  var QUAD_COLORS  = ['rgba(220,38,38,.11)','rgba(37,99,235,.11)','rgba(5,150,105,.11)','rgba(217,119,6,.11)'];
  var QUAD_BORDERS = ['rgba(220,38,38,.40)','rgba(37,99,235,.40)','rgba(5,150,105,.40)','rgba(217,119,6,.40)'];
  var QUAD_TEXTS   = ['#991b1b','#1e40af','#065f46','#92400e'];
  var CONFETTI_COLORS = ['#dc2626','#2563eb','#059669','#d97706','#7c3aed','#0891b2','#db2777'];

  function stanceToQuad(sx, sy) {
    return (sx >= 0 ? 1 : 0) + (sy < 0 ? 2 : 0);
  }
  function canvasToStance(cx, cy, W, H) {
    return { sx: (cx / W) * 4 - 2, sy: 2 - (cy / H) * 4 };
  }
  function stanceToCanvas(sx, sy, W, H) {
    return { cx: (sx + 2) / 4 * W, cy: (2 - sy) / 4 * H };
  }
  function dist2(ax, ay, bx, by) {
    var dx = ax - bx, dy = ay - by;
    return dx * dx + dy * dy;
  }
  function escHtml(s) {
    return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
  /* ページごとに変数名が RAW / SM_RAW / STANCE_POINTS と異なるため統一取得 */
  function getRawData() {
    /* jshint ignore:start */
    var r = (typeof RAW !== 'undefined') ? RAW            // eslint-disable-line no-undef
          : (typeof SM_RAW !== 'undefined') ? SM_RAW      // eslint-disable-line no-undef
          : (typeof STANCE_POINTS !== 'undefined') ? STANCE_POINTS // eslint-disable-line no-undef
          : null;
    /* jshint ignore:end */
    if (!r || !r.length) return null;
    /* フィールド名を {x,y,summary,url} に正規化 (RAW/SM_RAW は s/u 短縮) */
    return r.map(function (p) {
      return { x: p.x, y: p.y, summary: p.summary || p.s || '', url: p.url || p.u || '' };
    });
  }

  /* ---------- コンストラクタ ---------- */
  function Vote2D(cfg) {
    this.cfg        = cfg;
    this.pin        = null;
    this.voted      = false;
    this.stored     = {};
    this.myVote     = null;
    this.supa       = null;
    this.quizCorrect = null; // null=クイズ未表示, true/false=回答結果
    this.KEY        = 'sns_vote2d_v1_' + cfg.topic;
    this.TOPIC2D    = cfg.topic + '_2d_v1';

    if (cfg.supabaseUrl && cfg.supabaseAnonKey && typeof supabase !== 'undefined') {
      this.supa = supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey);
    }

    var saved = localStorage.getItem(this.KEY + '_my');
    this.myVote = saved ? JSON.parse(saved) : null;

    var self = this;

    var onReady = function (fn) {
      if (d.readyState === 'loading') {
        d.addEventListener('DOMContentLoaded', fn, { once: true });
      } else {
        fn();
      }
    };

    onReady(function () { self._applyBlur(); });
    this._buildCanvas();

    this._fetchVotes().then(function () {
      if (self.myVote !== null) {
        onReady(function () {
          if (w.setStanceMapVoteMarker) w.setStanceMapVoteMarker(self.myVote.qi, self.myVote.sx, self.myVote.sy);
        });
        self._showResults(self.myVote);
      }
    });
  }

  /* ---------- ブラー ---------- */
  Vote2D.prototype._applyBlur = function () {
    if (this.myVote !== null) return;
    var inner   = d.getElementById('stance-map-inner');
    var section = d.getElementById('stance-map-section');
    if (!inner || !section) return;
    inner.style.filter       = 'blur(8px)';
    inner.style.pointerEvents= 'none';
    inner.style.userSelect   = 'none';
    section.style.position   = 'relative';
    var ov = d.createElement('div');
    ov.id = 'chart-overlay';
    ov.style.cssText = 'position:absolute;inset:0;display:flex;align-items:center;' +
      'justify-content:center;z-index:5;background:rgba(255,255,255,.3);border-radius:8px;';
    ov.innerHTML = '<div style="text-align:center;">' +
      '<div style="font-size:16px;font-weight:800;color:var(--ink,#1a1a2e);">まず投票してから結果を見よう</div>' +
      '<div style="font-size:12px;color:var(--muted,#6b7280);margin-top:4px;">下の2D投票マップで立場を選んでください</div></div>';
    section.appendChild(ov);
  };

  Vote2D.prototype._revealChart = function () {
    var inner = d.getElementById('stance-map-inner');
    if (inner) {
      inner.style.transition   = 'filter .6s ease';
      inner.style.filter       = 'none';
      inner.style.pointerEvents= 'auto';
      inner.style.userSelect   = 'auto';
    }
    var ov = d.getElementById('chart-overlay');
    if (ov) ov.remove();
  };

  /* ---------- キャンバスUI構築 ---------- */
  Vote2D.prototype._buildCanvas = function () {
    var self = this;
    var cfg  = this.cfg;
    var wrap = d.getElementById(cfg.containerId || 'vote-buttons');
    if (!wrap) return;

    wrap.style.display = 'block';

    var H = w.innerWidth < 500 ? 210 : 270;

    wrap.innerHTML =
      '<div style="text-align:center;font-size:11px;color:var(--muted,#6b7280);margin-bottom:3px;">↑ ' + cfg.yAxis.pos + '</div>' +
      '<div style="display:flex;align-items:stretch;gap:4px;">' +
        '<div id="v2d-ylabel-l" style="font-size:9px;color:var(--muted,#6b7280);writing-mode:vertical-rl;' +
          'transform:rotate(180deg);white-space:nowrap;display:flex;align-items:center;">← ' + cfg.xAxis.neg + '</div>' +
        '<div style="flex:1;position:relative;">' +
          '<canvas id="v2d-canvas" style="display:block;width:100%;border-radius:10px;' +
            'border:1.5px solid var(--line,#e0e4ea);cursor:crosshair;touch-action:none;" height="' + H + '"></canvas>' +
          '<button id="v2d-confirm" style="display:none;position:absolute;bottom:10px;left:50%;' +
            'transform:translateX(-50%);background:var(--accent,#2563eb);color:#fff;border:none;' +
            'border-radius:20px;padding:7px 24px;font-size:13px;font-weight:700;cursor:pointer;' +
            'white-space:nowrap;z-index:10;box-shadow:0 4px 14px rgba(37,99,235,.35);">この位置で投票する ✓</button>' +
        '</div>' +
        '<div id="v2d-ylabel-r" style="font-size:9px;color:var(--muted,#6b7280);writing-mode:vertical-rl;' +
          'white-space:nowrap;display:flex;align-items:center;">' + cfg.xAxis.pos + ' →</div>' +
      '</div>' +
      '<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--muted,#6b7280);margin-top:3px;">' +
        '<span>← ' + cfg.xAxis.neg + '</span><span>' + cfg.xAxis.pos + ' →</span>' +
      '</div>' +
      '<div style="text-align:center;font-size:11px;color:var(--muted,#6b7280);margin-top:1px;">↓ ' + cfg.yAxis.neg + '</div>';

    var canvas = d.getElementById('v2d-canvas');
    var confirmBtn = d.getElementById('v2d-confirm');
    var dpr = w.devicePixelRatio || 1;
    var W   = Math.max(canvas.getBoundingClientRect().width || 360, 200);
    canvas.width  = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    this.canvas     = canvas;
    this.ctx        = ctx;
    this.cW         = W;
    this.cH         = H;
    this.confirmBtn = confirmBtn;

    this._draw();

    var self2 = this;
    requestAnimationFrame(function () {
      var trueW = canvas.getBoundingClientRect().width;
      if (trueW && Math.abs(trueW - self2.cW) > 4) {
        var H2  = trueW < 500 ? 210 : 270;
        self2.cW = trueW;
        self2.cH = H2;
        canvas.width  = Math.round(trueW * dpr);
        canvas.height = Math.round(H2   * dpr);
        canvas.style.height = H2 + 'px';
        var ctx2 = canvas.getContext('2d');
        ctx2.scale(dpr, dpr);
        self2.ctx = ctx2;
        self2._draw();
        if (self2.myVote) self2._showResults(self2.myVote);
      }
    });

    if (!this.myVote) {
      canvas.addEventListener('mousemove', function (e) {
        if (self.pin) return;
        var p = self._evPos(e);
        self._draw(p.x, p.y);
      });
      function onTap(e) {
        e.preventDefault();
        var src = e.touches ? e.changedTouches[0] : e;
        var p   = self._evPos(src);
        var st  = canvasToStance(p.x, p.y, self.cW, self.cH);
        self.pin = { cx: p.x, cy: p.y, sx: st.sx, sy: st.sy, qi: stanceToQuad(st.sx, st.sy) };
        self._draw();
        confirmBtn.style.display = 'block';
      }
      canvas.addEventListener('click', onTap);
      canvas.addEventListener('touchend', onTap, { passive: false });
      confirmBtn.addEventListener('click', function () { self._cast(); });
    }
  };

  Vote2D.prototype._evPos = function (e) {
    var r  = this.canvas.getBoundingClientRect();
    var sx = this.cW / r.width;
    var sy = this.cH / r.height;
    return { x: (e.clientX - r.left) * sx, y: (e.clientY - r.top) * sy };
  };

  /* ---------- 描画（pinScale: F ピンバウンス用） ---------- */
  Vote2D.prototype._draw = function (hx, hy, pinScale) {
    var ctx = this.ctx, W = this.cW, H = this.cH;
    var cfg = this.cfg;
    ctx.clearRect(0, 0, W, H);

    var hq = -1;
    if (hx !== undefined && !this.pin) {
      var hs = canvasToStance(hx, hy, W, H);
      hq = stanceToQuad(hs.sx, hs.sy);
    }

    [[0,0],[W/2,0],[0,H/2],[W/2,H/2]].forEach(function (pos, i) {
      ctx.fillStyle = (i === hq) ? QUAD_COLORS[i].replace('.11', '.22') : QUAD_COLORS[i];
      ctx.fillRect(pos[0], pos[1], W/2, H/2);
    });

    ctx.strokeStyle = 'rgba(140,140,160,.28)';
    ctx.lineWidth   = 1;
    ctx.setLineDash([4,4]);
    ctx.beginPath(); ctx.moveTo(W/2,0); ctx.lineTo(W/2,H); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0,H/2); ctx.lineTo(W,H/2); ctx.stroke();
    ctx.setLineDash([]);

    var quads   = cfg.quadrants;
    var corners = [[10,16,'left'],[W-10,16,'right'],[10,H-7,'left'],[W-10,H-7,'right']];
    corners.forEach(function (c, i) {
      ctx.font      = 'bold 10px -apple-system,sans-serif';
      ctx.textAlign = c[2];
      ctx.fillStyle = QUAD_TEXTS[i];
      ctx.fillText(quads[i] ? quads[i].label : '', c[0], c[1]);
    });

    if (!this.pin && !this.myVote) {
      ctx.font      = '11px -apple-system,sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = 'rgba(100,100,120,.45)';
      ctx.fillText('タップして自分の立場を置く', W/2, H/2 + 14);
    }

    if (hx !== undefined && !this.pin) {
      ctx.strokeStyle = 'rgba(37,99,235,.25)';
      ctx.lineWidth   = 1;
      ctx.setLineDash([3,3]);
      ctx.beginPath(); ctx.moveTo(hx,0); ctx.lineTo(hx,H); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0,hy); ctx.lineTo(W,hy); ctx.stroke();
      ctx.setLineDash([]);
    }

    var pin = this.pin;
    if (pin) {
      var scale = (pinScale !== undefined) ? pinScale : 1;
      ctx.save();
      ctx.translate(pin.cx, pin.cy);
      ctx.scale(scale, scale);
      ctx.translate(-pin.cx, -pin.cy);

      ctx.beginPath(); ctx.arc(pin.cx, pin.cy+3, 10, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(0,0,0,.14)'; ctx.fill();
      ctx.beginPath(); ctx.arc(pin.cx, pin.cy, 11, 0, Math.PI*2);
      ctx.fillStyle = '#2563eb'; ctx.fill();
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 2.5; ctx.stroke();
      ctx.font      = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = '#fff';
      ctx.fillText('あ', pin.cx, pin.cy + 4);

      ctx.restore();
    }
  };

  /* ---------- F: ピンバウンスアニメーション ---------- */
  Vote2D.prototype._drawPinBounce = function () {
    var self = this;
    var SCALES = [0, 0.45, 0.82, 1.22, 1.06, 0.94, 1.0];
    var i = 0;
    function step() {
      self._draw(undefined, undefined, SCALES[Math.min(i, SCALES.length - 1)]);
      i++;
      if (i < SCALES.length) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  };

  /* ---------- F: 紙吹雪 ---------- */
  Vote2D.prototype._confetti = function (anchorEl) {
    var rect = anchorEl ? anchorEl.getBoundingClientRect() : null;
    var cx   = rect ? (rect.left + rect.right) / 2 : w.innerWidth / 2;
    var cy   = rect ? (rect.top + rect.bottom) / 2 + w.scrollY : w.innerHeight / 2 + w.scrollY;
    for (var i = 0; i < 50; i++) {
      (function (i) {
        setTimeout(function () {
          var el = d.createElement('div');
          var color   = CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)];
          var isRound = Math.random() > 0.4;
          el.style.cssText =
            'position:absolute;pointer-events:none;z-index:99999;' +
            'width:8px;height:8px;border-radius:' + (isRound ? '50%' : '2px') + ';' +
            'background:' + color + ';' +
            'left:' + cx + 'px;top:' + cy + 'px;' +
            'transform:translate(-50%,-50%);opacity:1;';
          d.body.appendChild(el);

          var dx   = (Math.random() - 0.5) * 380;
          var dy   = -Math.random() * 300 - 80;
          var rot  = Math.random() * 720 - 360;
          var dur  = 750 + Math.random() * 450;

          setTimeout(function () {
            el.style.transition = 'transform ' + dur + 'ms cubic-bezier(.25,.46,.45,.94), opacity ' + dur + 'ms ease';
            el.style.transform  = 'translate(calc(-50% + ' + dx + 'px), calc(-50% + ' + dy + 'px)) rotate(' + rot + 'deg) scale(0)';
            el.style.opacity    = '0';
          }, 16);

          setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, dur + 200);
        }, i * 18);
      })(i);
    }
  };

  /* ---------- 投票送信 ---------- */
  Vote2D.prototype._cast = function () {
    if (!this.pin || this.voted) return;
    this.voted = true;
    this.confirmBtn.style.display = 'none';

    var self = this;
    var pin  = this.pin;
    var data = { topic_id: this.TOPIC2D, choice_idx: pin.qi };

    var finish = function () {
      var voteData = { qi: pin.qi, sx: Math.round(pin.sx*100)/100, sy: Math.round(pin.sy*100)/100 };
      localStorage.setItem(self.KEY + '_my', JSON.stringify(voteData));
      self.myVote = voteData;
      self._revealChart();
      if (w.setStanceMapVoteMarker) w.setStanceMapVoteMarker(pin.qi, pin.sx, pin.sy);
      self._drawPinBounce();
      self._showQuiz(voteData);
    };

    if (this.supa) {
      this.supa.from('votes').insert([data]).then(function (res) {
        if (res.error) {
          var msg = (res.error.message || '') + (res.error.details || '');
          if (msg.indexOf('already voted') !== -1 || (res.error.code === '23505')) {
            alert('24時間以内に同じIPからすでに投票されています。集計結果のみ表示します。');
          }
        }
        self._fetchVotes().then(finish);
      });
    } else {
      var counts = JSON.parse(localStorage.getItem(this.KEY + '_counts') || '{}');
      counts[pin.qi] = (counts[pin.qi] || 0) + 1;
      localStorage.setItem(this.KEY + '_counts', JSON.stringify(counts));
      this.stored = counts;
      finish();
    }
  };

  /* ---------- 集計取得 ---------- */
  Vote2D.prototype._fetchVotes = function () {
    var self = this;
    if (this.supa) {
      return this.supa.from('votes').select('choice_idx').eq('topic_id', this.TOPIC2D)
        .then(function (res) {
          if (res.error) { self._loadLocal(); return; }
          self.stored = {};
          (res.data || []).forEach(function (r) {
            var i = r.choice_idx;
            if (i !== null && i !== undefined) self.stored[i] = (self.stored[i]||0)+1;
          });
        }).catch(function () { self._loadLocal(); });
    }
    this._loadLocal();
    return Promise.resolve();
  };

  Vote2D.prototype._loadLocal = function () {
    this.stored = JSON.parse(localStorage.getItem(this.KEY + '_counts') || '{}');
  };

  /* ---------- A: クイズ表示 ---------- */
  Vote2D.prototype._showQuiz = function (vote) {
    var self = this;
    var cfg  = this.cfg;

    var raw = getRawData();

    if (!raw || raw.length < 4) {
      this._showResults(vote);
      return;
    }

    var snsCounts = [0, 0, 0, 0];
    for (var ri = 0; ri < raw.length; ri++) {
      snsCounts[stanceToQuad(raw[ri].x, raw[ri].y)]++;
    }
    var snsTotal = raw.length;
    var maxCount = Math.max.apply(null, snsCounts);
    if (maxCount === 0) { this._showResults(vote); return; }
    var correctQi = snsCounts.indexOf(maxCount);

    var res = d.getElementById(cfg.resultId || 'vote-result');
    if (!res) { this._showResults(vote); return; }

    var quizDiv = d.createElement('div');
    quizDiv.id = 'vote2d-quiz';

    var quads  = cfg.quadrants;
    var btnHtml = '';
    for (var q = 0; q < 4; q++) {
      var col = QUAD_BORDERS[q].replace('.40', '.85');
      var bg  = QUAD_COLORS[q];
      btnHtml +=
        '<button type="button" data-qi="' + q + '" ' +
          'style="border:1.5px solid ' + col + ';border-radius:8px;background:' + bg + ';' +
          'padding:10px 14px;font-size:13px;font-weight:700;cursor:pointer;text-align:left;' +
          'color:' + QUAD_TEXTS[q] + ';transition:transform .15s ease,box-shadow .15s ease;">' +
          escHtml(quads[q] ? quads[q].label : 'Q' + q) +
        '</button>';
    }

    quizDiv.innerHTML =
      '<div style="background:var(--accent-soft,#f0faf5);border-radius:10px;padding:16px 18px;margin-bottom:16px;">' +
        '<div style="font-size:14px;font-weight:800;color:var(--ink,#1a1a2e);margin-bottom:10px;">' +
          '開票前に予想！　SNSで最多だった立場は？' +
        '</div>' +
        '<div id="v2d-quiz-btns" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;">' +
          btnHtml +
        '</div>' +
        '<div id="v2d-quiz-result" style="display:none;margin-top:12px;"></div>' +
        '<div id="v2d-quiz-continue" style="display:none;margin-top:12px;">' +
          '<button type="button" id="v2d-quiz-next" ' +
            'style="background:var(--accent,#2563eb);color:#fff;border:none;border-radius:8px;' +
            'padding:8px 22px;font-size:13px;font-weight:700;cursor:pointer;">' +
            '結果を見る →' +
          '</button>' +
        '</div>' +
      '</div>';

    res.parentNode.insertBefore(quizDiv, res);

    if (w.gtag) w.gtag('event', 'vote2d_quiz_shown', { topic: cfg.topic });

    var btns = quizDiv.querySelectorAll('[data-qi]');
    var answered = false;
    function onQuizClick(e) {
      if (answered) return;
      answered = true;
      var btn    = e.currentTarget;
      var chosen = parseInt(btn.getAttribute('data-qi'), 10);
      for (var b = 0; b < btns.length; b++) {
        btns[b].disabled = true;
        btns[b].style.opacity = '0.5';
      }
      btn.style.opacity   = '1';
      btn.style.transform = 'scale(1.04)';
      self._evaluateQuiz(chosen, correctQi, snsCounts, maxCount, snsTotal, vote, quizDiv);
    }
    for (var b = 0; b < btns.length; b++) {
      btns[b].addEventListener('click', onQuizClick);
    }
  };

  /* ---------- A: クイズ答え合わせ ---------- */
  Vote2D.prototype._evaluateQuiz = function (chosen, correctQi, snsCounts, maxCount, snsTotal, vote, quizDiv) {
    var self      = this;
    var cfg       = this.cfg;
    var quads     = cfg.quadrants;
    var isCorrect = (chosen === correctQi);
    this.quizCorrect = isCorrect;

    var correctLabel = quads[correctQi] ? quads[correctQi].label : '';
    var pct          = snsTotal > 0 ? Math.round(maxCount / snsTotal * 100) : 0;
    var col          = QUAD_BORDERS[correctQi].replace('.40', '.85');
    var bg           = QUAD_COLORS[correctQi];

    var resultDiv = d.getElementById('v2d-quiz-result');
    if (!resultDiv) return;

    if (isCorrect) {
      resultDiv.innerHTML =
        '<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:8px;' +
          'background:' + bg + ';border:1.5px solid ' + col + ';">' +
          '<span style="font-size:22px;line-height:1;" aria-hidden="true">&#x1F389;</span>' +
          '<div>' +
            '<div style="font-size:14px;font-weight:800;color:' + col + ';">正解！</div>' +
            '<div style="font-size:12px;color:' + QUAD_TEXTS[correctQi] + ';margin-top:2px;">' +
              'SNS最多は「' + escHtml(correctLabel) + '」 ' + pct + '%（' + maxCount + '/' + snsTotal + '件）' +
            '</div>' +
          '</div>' +
        '</div>';
      this._confetti(quizDiv);
    } else {
      resultDiv.innerHTML =
        '<div style="padding:10px 14px;border-radius:8px;background:var(--panel,#f5f7f5);' +
          'border:1px solid var(--line,#e0e4ea);">' +
          '<div style="font-size:13px;font-weight:700;color:var(--ink,#1a1a2e);">惜しかった！</div>' +
          '<div style="font-size:12px;color:var(--muted,#6b7280);margin-top:4px;">' +
            'SNS最多は「<strong style="color:' + col + '">' + escHtml(correctLabel) + '</strong>」 ' +
            pct + '%（' + maxCount + '/' + snsTotal + '件）' +
          '</div>' +
        '</div>';
    }

    resultDiv.style.display = 'block';

    var cont = d.getElementById('v2d-quiz-continue');
    if (cont) cont.style.display = 'block';

    if (w.gtag) w.gtag('event', 'vote2d_quiz_answered', { topic: cfg.topic, correct: isCorrect });

    var nextBtn = d.getElementById('v2d-quiz-next');
    if (nextBtn) {
      nextBtn.addEventListener('click', function () {
        var qBlock = d.getElementById('vote2d-quiz');
        if (qBlock) qBlock.remove();
        self._showResults(vote);
      });
    }
  };

  /* ---------- 結果表示 ---------- */
  Vote2D.prototype._showResults = function (vote) {
    var self   = this;
    var cfg    = this.cfg;
    var quads  = cfg.quadrants;
    var q      = quads[vote.qi] || quads[0];
    var color  = QUAD_BORDERS[vote.qi].replace('.40','.85');

    if (this.canvas && vote.sx !== undefined) {
      var cp = stanceToCanvas(vote.sx, vote.sy, this.cW, this.cH);
      this.pin = { cx: cp.cx, cy: cp.cy, sx: vote.sx, sy: vote.sy, qi: vote.qi };
      this._draw();
    }

    var total = 0;
    for (var k in this.stored) total += (this.stored[k]||0);
    if (total === 0) total = 1;

    var lbl = d.getElementById('vote-position-label');
    if (lbl) { lbl.textContent = 'あなたの立場: 「' + q.label + '」'; lbl.style.color = color; }
    var txt = d.getElementById('vote-position-text');
    if (txt) txt.textContent = (q.desc || '') +
      '\n\nXY軸上の座標—— ' + cfg.xAxis.neg + '/' + cfg.xAxis.pos + ' 軸: ' +
      (vote.sx >= 0 ? '+' : '') + vote.sx.toFixed(1) + ' ／ ' +
      cfg.yAxis.neg + '/' + cfg.yAxis.pos + ' 軸: ' +
      (vote.sy >= 0 ? '+' : '') + vote.sy.toFixed(1);

    var comp = d.getElementById('vote-comparison');
    if (comp) {
      var hdr = comp.previousElementSibling;
      if (hdr) hdr.style.display = 'none';
      comp.style.display = 'none';
    }
    var bars = d.getElementById('vote-bars');
    if (bars) bars.style.display = 'none';

    var quizCorrect = this.quizCorrect;

    (function insertSnsSection() {
      var rawData = getRawData();
      if (!rawData) {
        if (d.readyState === 'loading') {
          d.addEventListener('DOMContentLoaded', insertSnsSection, { once: true });
        }
        return;
      }
      if (!rawData.length) return;

      var snsTotal  = rawData.length;
      var snsCounts = [0, 0, 0, 0];
      for (var ri = 0; ri < rawData.length; ri++) {
        snsCounts[stanceToQuad(rawData[ri].x, rawData[ri].y)]++;
      }
      var mySnsPct = Math.round(snsCounts[vote.qi] / snsTotal * 100);

      var voteTotal = 0;
      for (var vk in self.stored) voteTotal += (self.stored[vk] || 0);

      var snsDist = d.getElementById('vote-sns-dist');
      if (!snsDist) {
        snsDist = d.createElement('div');
        snsDist.id = 'vote-sns-dist';
        if (comp) {
          comp.parentNode.insertBefore(snsDist, comp);
        } else if (bars) {
          bars.parentNode.insertBefore(snsDist, bars);
        }
      }

      var snsHtml =
        '<div style="font-size:14px;font-weight:700;color:var(--ink,#1a1a2e);margin-bottom:4px;">' +
          'X上の声の分布（SNS分類 ' + snsTotal + '件）</div>' +
        '<div style="font-size:12px;color:var(--muted,#667085);margin-bottom:14px;">' +
          'あなたと同じ「' + q.label + '」は ' +
          '<strong style="color:' + color + '">' + mySnsPct + '%（' + snsCounts[vote.qi] + '件）</strong>' +
        '</div>';

      quads.forEach(function (qq, i) {
        var c      = snsCounts[i];
        var pct    = Math.round(c / snsTotal * 100);
        var col    = QUAD_BORDERS[i].replace('.40', '.85');
        var colBg  = QUAD_COLORS[i];
        var mine   = i === vote.qi;
        snsHtml +=
          '<div style="margin-bottom:8px;padding:' + (mine ? '8px 10px' : '5px 10px') + ';' +
            'border-radius:6px;background:' + (mine ? colBg : 'transparent') + ';' +
            'border-left:3px solid ' + (mine ? col : 'transparent') + ';">' +
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">' +
              '<span style="font-size:12px;font-weight:' + (mine ? '700' : '400') + ';color:' +
                (mine ? col : 'var(--muted,#667085)') + ';display:flex;align-items:center;gap:6px;">' +
                escHtml(qq.label) +
                (mine
                  ? ' <span style="font-size:10px;font-weight:600;padding:2px 6px;border-radius:4px;' +
                    'background:' + col + ';color:#fff;white-space:nowrap;">あなた</span>'
                  : '') +
              '</span>' +
              '<span style="font-size:12px;font-weight:' + (mine ? '700' : '400') + ';color:' +
                (mine ? col : 'var(--muted,#667085)') + '">' + pct + '%（' + c + '件）</span>' +
            '</div>' +
            '<div style="height:6px;border-radius:3px;background:var(--line,#e0e4ea);overflow:hidden;">' +
              '<div id="sns-bar-' + i + '" style="height:100%;width:0%;background:' + col +
                ';border-radius:3px;transition:width .7s ease ' + (i * 0.1) + 's;opacity:' + (mine ? '1' : '0.4') + ';"></div>' +
            '</div>' +
          '</div>';
      });

      if (voteTotal > 0) {
        snsHtml +=
          '<div style="font-size:11px;color:var(--muted,#888);margin-top:12px;' +
            'padding:8px 12px;background:var(--panel,#f5f5f5);border-radius:6px;line-height:1.5;">' +
            'あなたの投票が集計に追加されました。現在 <strong>' + voteTotal + '票</strong> が集まっています。' +
          '</div>';
      }

      snsDist.innerHTML = snsHtml;

      /* F: バーアニメーション（次フレームで幅を設定して transition を発火） */
      requestAnimationFrame(function () {
        for (var bi = 0; bi < 4; bi++) {
          var barEl = d.getElementById('sns-bar-' + bi);
          if (barEl) {
            var bpct = Math.round(snsCounts[bi] / snsTotal * 100);
            barEl.style.width = bpct + '%';
          }
        }
      });

      /* B: 近い声・遠い声（SNS dist の直後に挿入） */
      self._showNearFar(vote, rawData, snsDist);
    }());

    /* Xシェア */
    var shareBtn = d.getElementById('share-x');
    if (shareBtn) {
      var posStr = (vote.sx >= 0 ? 'やや右' : 'やや左') + '・' + (vote.sy >= 0 ? '上寄り' : '下寄り');
      var shareText;
      if (quizCorrect === true) {
        shareText = '[開票前の予想的中！]\n' +
          cfg.title + 'でSNS世論を1発で当てました。\n私の立場: 「' + q.label + '」\n\nあなたも試してみて。\n\n#SNS反応まっぷ';
      } else {
        shareText = '[「' + cfg.title + '」]\n私の立場: 「' + q.label + '」（' + posStr + '）\n\nSNSの声の分布と比べてみて。\n\n#SNS反応まっぷ';
      }
      var url  = location.href.split('#')[0].split('?')[0]+'?utm_source=share_button&utm_medium=social&utm_campaign=vote_share';
      shareBtn.href = 'https://x.com/intent/tweet?text='+encodeURIComponent(shareText)+'&url='+encodeURIComponent(url);
      var short = q.label.length > 14 ? q.label.slice(0,14)+'…' : q.label;
      shareBtn.textContent = '𝕏 でシェア「'+short+'」' + (quizCorrect === true ? ' ★的中' : '');
    }

    var redo = d.getElementById('vote-redo-btn');
    if (redo) {
      if (self.supa) { redo.style.display = 'none'; }
      else { redo.onclick = function () { localStorage.removeItem(self.KEY+'_my'); location.reload(); }; }
    }

    var res = d.getElementById(cfg.resultId || 'vote-result');
    if (res) res.style.display = 'block';

    document.dispatchEvent(new CustomEvent('vote2d:revealed'));
  };

  /* ---------- B: 近い声・遠い声 ---------- */
  Vote2D.prototype._showNearFar = function (vote, rawData, snsDist) {
    var cfg = this.cfg;

    if (!rawData || rawData.length < 2 || !snsDist) return;

    var minD = Infinity, maxD = -1;
    var nearPt = null, farPt = null;

    for (var i = 0; i < rawData.length; i++) {
      var r = rawData[i];
      if (!r.summary || !r.summary.trim()) continue;
      var d2 = dist2(vote.sx, vote.sy, r.x, r.y);
      if (d2 < minD || (d2 === minD && nearPt && r.summary.length > nearPt.summary.length)) {
        minD = d2; nearPt = r;
      }
      if (d2 > maxD || (d2 === maxD && farPt && r.summary.length > farPt.summary.length)) {
        maxD = d2; farPt = r;
      }
    }

    if (!nearPt || !farPt) return;

    var nearQi    = stanceToQuad(nearPt.x, nearPt.y);
    var farQi     = stanceToQuad(farPt.x,  farPt.y);
    var nearCol   = QUAD_BORDERS[nearQi].replace('.40', '.85');
    var farCol    = QUAD_BORDERS[farQi].replace('.40', '.85');
    var nearBg    = QUAD_COLORS[nearQi];
    var farBg     = QUAD_COLORS[farQi];
    var nearLabel = cfg.quadrants[nearQi] ? cfg.quadrants[nearQi].label : '';
    var farLabel  = cfg.quadrants[farQi]  ? cfg.quadrants[farQi].label  : '';
    var nearDist  = Math.round(Math.sqrt(minD) * 10) / 10;
    var farDist   = Math.round(Math.sqrt(maxD) * 10) / 10;

    function cardHtml(pt, col, bg, label, dist, isNear) {
      var titleText = isNear
        ? 'あなたに一番近い声'
        : '一番遠くにある声';
      var linkHtml = pt.url
        ? ' <a href="' + escHtml(pt.url) + '" target="_blank" rel="noopener" ' +
          'style="font-size:11px;color:' + col + ';text-decoration:underline;">→ Xで見る</a>'
        : '';
      return '<div style="border-radius:10px;background:' + escHtml(bg) + ';border:1.5px solid ' + escHtml(col) + ';padding:14px;">' +
        '<div style="font-size:12px;font-weight:800;color:' + escHtml(col) + ';margin-bottom:6px;">' +
          (isNear ? '●' : '□') + ' ' + titleText +
        '</div>' +
        '<div style="font-size:13px;color:var(--ink,#1a1a2e);line-height:1.55;margin-bottom:8px;">' +
          '「' + escHtml(pt.summary) + '」' +
        '</div>' +
        '<div style="font-size:11px;color:' + escHtml(col) + ';">' +
          escHtml(label) + ' / 距離 ' + dist + linkHtml +
        '</div>' +
      '</div>';
    }

    var nfDiv = d.createElement('div');
    nfDiv.id = 'vote2d-nearfar';
    nfDiv.style.cssText = 'margin-top:16px;';
    nfDiv.innerHTML =
      '<div style="font-size:14px;font-weight:800;color:var(--ink,#1a1a2e);margin-bottom:10px;">' +
        'あなたの立場から見たリアルな声' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;">' +
        cardHtml(nearPt, nearCol, nearBg, nearLabel, nearDist, true) +
        cardHtml(farPt,  farCol,  farBg,  farLabel,  farDist,  false) +
      '</div>';

    snsDist.parentNode.insertBefore(nfDiv, snsDist.nextSibling);
  };

  /* ---------- 公開API ---------- */
  w.Vote2D = {
    /**
     * cfg: {
     *   containerId: string,
     *   resultId: string,
     *   topic: string,
     *   title: string,
     *   xAxis: { neg: string, pos: string },
     *   yAxis: { neg: string, pos: string },
     *   quadrants: [{ label: string, desc: string }, ...],
     *   supabaseUrl: string,
     *   supabaseAnonKey: string,
     * }
     */
    init: function (cfg) { return new Vote2D(cfg); }
  };

}(window, document));
