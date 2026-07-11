/*!
 * vote2d.js — 2D キャンバス投票コンポーネント
 * 使い方: Vote2D.init(config) を呼ぶだけ。詳細は下記 init() の cfg 参照。
 */
(function (w, d) {
  'use strict';

  /* ---------- 定数 ---------- */
  var QUAD_COLORS  = ['rgba(220,38,38,.11)','rgba(37,99,235,.11)','rgba(5,150,105,.11)','rgba(217,119,6,.11)'];
  var QUAD_BORDERS = ['rgba(220,38,38,.40)','rgba(37,99,235,.40)','rgba(5,150,105,.40)','rgba(217,119,6,.40)'];
  var QUAD_TEXTS   = ['#991b1b','#1e40af','#065f46','#92400e'];

  /* quadrant index: 0=TL 1=TR 2=BL 3=BR
     stanceX<0 & stanceY>=0 → TL(0)
     stanceX>=0 & stanceY>=0 → TR(1)
     stanceX<0 & stanceY<0  → BL(2)
     stanceX>=0 & stanceY<0 → BR(3)  */
  function stanceToQuad(sx, sy) {
    return (sx >= 0 ? 1 : 0) + (sy < 0 ? 2 : 0);
  }
  function canvasToStance(cx, cy, W, H) {
    return { sx: (cx / W) * 4 - 2, sy: 2 - (cy / H) * 4 };
  }
  function stanceToCanvas(sx, sy, W, H) {
    return { cx: (sx + 2) / 4 * W, cy: (2 - sy) / 4 * H };
  }

  /* ---------- コンストラクタ ---------- */
  function Vote2D(cfg) {
    this.cfg     = cfg;
    this.pin     = null;
    this.voted   = false;
    this.stored  = {};
    this.myVote  = null;
    this.supa    = null;
    this.KEY     = 'sns_vote2d_v1_' + cfg.topic;
    this.TOPIC2D = cfg.topic + '_2d_v1';

    if (cfg.supabaseUrl && cfg.supabaseAnonKey && typeof supabase !== 'undefined') {
      this.supa = supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey);
    }

    var saved = localStorage.getItem(this.KEY + '_my');
    this.myVote = saved ? JSON.parse(saved) : null;

    var self = this;

    /* #stance-map-* や setStanceMapVoteMarker はこのスクリプトより後の
       HTML/<script> で定義されるため、DOM 構築完了後に実行する */
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

    /* Resize to actual CSS dimensions after layout — fixes blurry canvas
       when clientWidth is 0 at synchronous script execution time */
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

  /* ---------- 描画 ---------- */
  Vote2D.prototype._draw = function (hx, hy) {
    var ctx = this.ctx, W = this.cW, H = this.cH;
    var cfg = this.cfg;
    ctx.clearRect(0, 0, W, H);

    var hq = -1;
    if (hx !== undefined && !this.pin) {
      var hs = canvasToStance(hx, hy, W, H);
      hq = stanceToQuad(hs.sx, hs.sy);
    }

    /* 象限塗り */
    [[0,0],[W/2,0],[0,H/2],[W/2,H/2]].forEach(function (pos, i) {
      ctx.fillStyle = (i === hq) ? QUAD_COLORS[i].replace('.11', '.22') : QUAD_COLORS[i];
      ctx.fillRect(pos[0], pos[1], W/2, H/2);
    });

    /* グリッド線 */
    ctx.strokeStyle = 'rgba(140,140,160,.28)';
    ctx.lineWidth   = 1;
    ctx.setLineDash([4,4]);
    ctx.beginPath(); ctx.moveTo(W/2,0); ctx.lineTo(W/2,H); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0,H/2); ctx.lineTo(W,H/2); ctx.stroke();
    ctx.setLineDash([]);

    /* 象限ラベル（四隅） */
    var quads   = cfg.quadrants;
    var corners = [[10,16,'left'],[W-10,16,'right'],[10,H-7,'left'],[W-10,H-7,'right']];
    corners.forEach(function (c, i) {
      ctx.font      = 'bold 10px -apple-system,sans-serif';
      ctx.textAlign = c[2];
      ctx.fillStyle = QUAD_TEXTS[i];
      ctx.fillText(quads[i] ? quads[i].label : '', c[0], c[1]);
    });

    /* ヒント文字 */
    if (!this.pin && !this.myVote) {
      ctx.font      = '11px -apple-system,sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = 'rgba(100,100,120,.45)';
      ctx.fillText('タップして自分の立場を置く', W/2, H/2 + 14);
    }

    /* ホバー十字線 */
    if (hx !== undefined && !this.pin) {
      ctx.strokeStyle = 'rgba(37,99,235,.25)';
      ctx.lineWidth   = 1;
      ctx.setLineDash([3,3]);
      ctx.beginPath(); ctx.moveTo(hx,0); ctx.lineTo(hx,H); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0,hy); ctx.lineTo(W,hy); ctx.stroke();
      ctx.setLineDash([]);
    }

    /* ピン */
    var pin = this.pin;
    if (pin) {
      ctx.beginPath(); ctx.arc(pin.cx, pin.cy+3, 10, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(0,0,0,.14)'; ctx.fill();
      ctx.beginPath(); ctx.arc(pin.cx, pin.cy, 11, 0, Math.PI*2);
      ctx.fillStyle = '#2563eb'; ctx.fill();
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 2.5; ctx.stroke();
      ctx.font      = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = '#fff';
      ctx.fillText('あ', pin.cx, pin.cy + 4);
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
      self._draw();
      self._showResults(voteData);
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

  /* ---------- 結果表示 ---------- */
  Vote2D.prototype._showResults = function (vote) {
    var self   = this;
    var cfg    = this.cfg;
    var quads  = cfg.quadrants;
    var q      = quads[vote.qi] || quads[0];
    var color  = QUAD_BORDERS[vote.qi].replace('.40','.85');

    /* キャンバスにピンを復元 */
    if (this.canvas && vote.sx !== undefined) {
      var cp = stanceToCanvas(vote.sx, vote.sy, this.cW, this.cH);
      this.pin = { cx: cp.cx, cy: cp.cy, sx: vote.sx, sy: vote.sy, qi: vote.qi };
      this._draw();
    }

    var total = 0;
    for (var k in this.stored) total += (this.stored[k]||0);
    if (total === 0) total = 1;

    /* 位置ラベル */
    var lbl = d.getElementById('vote-position-label');
    if (lbl) { lbl.textContent = 'あなたの立場: 「' + q.label + '」'; lbl.style.color = color; }
    var txt = d.getElementById('vote-position-text');
    if (txt) txt.textContent = (q.desc || '') +
      '\n\nXY軸上の座標 — ' + cfg.xAxis.neg + '/' + cfg.xAxis.pos + ' 軸: ' +
      (vote.sx >= 0 ? '+' : '') + vote.sx.toFixed(1) + ' ／ ' +
      cfg.yAxis.neg + '/' + cfg.yAxis.pos + ' 軸: ' +
      (vote.sy >= 0 ? '+' : '') + vote.sy.toFixed(1);

    /* 比較カード */
    var comp = d.getElementById('vote-comparison');
    if (comp) {
      var myPct = Math.round((self.stored[vote.qi]||0)/total*100);
      comp.innerHTML =
        '<div class="vote-compare-card"><b>あなたの立場</b>' +
          '<span style="font-weight:900;color:'+color+'">'+q.label+'</span></div>'+
        '<div class="vote-compare-card"><b>同じ立場の投票者</b>' +
          '<span style="font-weight:900;color:'+color+'">'+myPct+'% ('+(self.stored[vote.qi]||0)+'票)</span></div>';
    }

    /* バーチャート */
    var bars = d.getElementById('vote-bars');
    if (bars) {
      bars.innerHTML = '';
      quads.forEach(function (qq, i) {
        var c   = self.stored[i] || 0;
        var pct = Math.round(c / total * 100);
        var col = QUAD_BORDERS[i].replace('.40','.85');
        var mine = i === vote.qi;
        var row = d.createElement('div');
        row.style.marginBottom = '8px';
        row.innerHTML =
          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">' +
            '<span style="font-size:12px;font-weight:'+(mine?'800':'600')+';color:'+(mine?col:'var(--ink,#1a1a2e)')+'">' +
              (mine?'✓ ':'')+qq.label+'</span>'+
            '<span style="font-size:13px;font-weight:800;color:'+col+'">'+pct+'% ('+c+'票)</span></div>'+
          '<div style="height:8px;border-radius:4px;background:var(--line,#e0e4ea);overflow:hidden;">'+
            '<div style="height:100%;width:'+pct+'%;background:'+col+
              ';border-radius:4px;transition:width .5s ease;"></div></div>';
        bars.appendChild(row);
      });
    }

    /* SNS分類データがある場合: Xの声の分布を vote-bars の直後に挿入
     * RAWはconstのためwindowプロパティにならずスコープ直参照が必要。
     * 返訪者では_showResultsがDOMContentLoaded前に呼ばれるためRAWが未定義の場合は
     * DOMContentLoaded後に再実行する。 */
    (function insertSnsSection() {
      /* jshint ignore:start */
      var rawData = (typeof RAW !== 'undefined') ? RAW : null; // eslint-disable-line no-undef
      /* jshint ignore:end */
      if (!rawData) {
        if (d.readyState === 'loading') {
          d.addEventListener('DOMContentLoaded', insertSnsSection, { once: true });
        }
        return;
      }
      if (!bars || !rawData.length) return;

      var snsTotal  = rawData.length;
      var snsCounts = [0, 0, 0, 0];
      for (var ri = 0; ri < rawData.length; ri++) {
        snsCounts[stanceToQuad(rawData[ri].x, rawData[ri].y)]++;
      }
      var mySnsPct = Math.round(snsCounts[vote.qi] / snsTotal * 100);

      var snsDist = d.getElementById('vote-sns-dist');
      if (!snsDist) {
        snsDist = d.createElement('div');
        snsDist.id = 'vote-sns-dist';
        bars.parentNode.insertBefore(snsDist, bars.nextSibling);
      }

      var snsHtml =
        '<div style="font-size:13px;font-weight:700;color:var(--muted,#667085);' +
          'margin:16px 0 8px;border-top:1px solid var(--line,#e0e4ea);padding-top:16px;">' +
          'Xの声の分布（SNS分類 ' + snsTotal + '件）</div>' +
        '<div style="font-size:12px;color:var(--muted,#667085);margin-bottom:10px;">' +
          'あなたと同じ「' + q.label + '」は ' +
          '<strong style="color:' + color + '">' + mySnsPct + '%（' + snsCounts[vote.qi] + '件）</strong>' +
        '</div>';
      quads.forEach(function (qq, i) {
        var c    = snsCounts[i];
        var pct  = Math.round(c / snsTotal * 100);
        var col  = QUAD_BORDERS[i].replace('.40', '.85');
        var mine = i === vote.qi;
        snsHtml +=
          '<div style="margin-bottom:7px;">' +
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">' +
              '<span style="font-size:11px;font-weight:' + (mine ? '800' : '500') + ';color:' +
                (mine ? col : 'var(--muted,#667085)') + '">' + (mine ? '✓ ' : '') + qq.label + '</span>' +
              '<span style="font-size:12px;font-weight:700;color:' + col + '">' + pct + '%（' + c + '件）</span>' +
            '</div>' +
            '<div style="height:6px;border-radius:3px;background:var(--line,#e0e4ea);overflow:hidden;">' +
              '<div style="height:100%;width:' + pct + '%;background:' + col +
                ';border-radius:3px;transition:width .6s ease;"></div>' +
            '</div>' +
          '</div>';
      });
      snsDist.innerHTML = snsHtml;
    }());

    /* Xシェア */
    var shareBtn = d.getElementById('share-x');
    if (shareBtn) {
      var posStr = (vote.sx >= 0 ? 'やや右' : 'やや左') + '・' + (vote.sy >= 0 ? '上寄り' : '下寄り');
      var text = '【'+cfg.title+'】\n私の立場: 「'+q.label+'」（'+posStr+'）\n\nあなたはどこ？ SNSの声の分布と比べてみて。\n\n#SNS反応まっぷ';
      var url  = location.href.split('#')[0].split('?')[0]+'?utm_source=share_button&utm_medium=social&utm_campaign=vote_share';
      shareBtn.href = 'https://x.com/intent/tweet?text='+encodeURIComponent(text)+'&url='+encodeURIComponent(url);
      var short = q.label.length > 14 ? q.label.slice(0,14)+'…' : q.label;
      shareBtn.textContent = '𝕏 でシェア「'+short+'」';
    }

    /* やり直しボタン */
    var redo = d.getElementById('vote-redo-btn');
    if (redo) {
      if (self.supa) { redo.style.display = 'none'; }
      else { redo.onclick = function () { localStorage.removeItem(self.KEY+'_my'); location.reload(); }; }
    }

    /* 結果エリア表示 */
    var res = d.getElementById(cfg.resultId || 'vote-result');
    if (res) res.style.display = 'block';
  };

  /* ---------- 公開API ---------- */
  w.Vote2D = {
    /**
     * cfg: {
     *   containerId: string,          // #vote-buttons
     *   resultId: string,             // #vote-result
     *   topic: string,                // Supabase topic_id ベース
     *   title: string,                // シェア文用タイトル
     *   xAxis: { neg: string, pos: string },  // 左←→右
     *   yAxis: { neg: string, pos: string },  // 下←→上
     *   quadrants: [                  // [TL, TR, BL, BR]
     *     { label: string, desc: string },
     *     ...
     *   ],
     *   supabaseUrl: string,
     *   supabaseAnonKey: string,
     * }
     */
    init: function (cfg) { return new Vote2D(cfg); }
  };

}(window, document));
