/*!
 * vote-store.js — 全テーマ共通の投票保存クライアント
 */
(function (window) {
  'use strict';

  var config = window.SNS_VOTE_CONFIG || {};
  var supabaseUrl = String(config.supabaseUrl || '').replace(/\/$/, '');
  var publishableKey = String(config.publishableKey || '');
  var remoteEnabled = /^https:\/\//.test(supabaseUrl) && publishableKey.length > 0;
  var endpoint = remoteEnabled ? supabaseUrl + '/functions/v1/cast-vote' : '';

  function parseSaved(storageKey) {
    try {
      return JSON.parse(localStorage.getItem(storageKey) || 'null');
    } catch (error) {
      localStorage.removeItem(storageKey);
      return null;
    }
  }

  function persist(storageKey, value) {
    localStorage.setItem(storageKey, JSON.stringify(value));
  }

  function request(url, options) {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, 10000);
    var requestOptions = Object.assign({}, options, {
      signal: controller.signal,
      headers: Object.assign({
        'apikey': publishableKey,
        'Authorization': 'Bearer ' + publishableKey,
        'Content-Type': 'application/json'
      }, options && options.headers)
    });
    return fetch(url, requestOptions).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (body) {
        if (!response.ok) {
          var error = new Error(body.error || 'vote_request_failed');
          error.status = response.status;
          throw error;
        }
        return body;
      });
    }).finally(function () {
      clearTimeout(timer);
    });
  }

  function cast(options) {
    if (!options || !options.topicId || !Number.isInteger(options.choiceIdx)) {
      return Promise.reject(new Error('invalid_vote'));
    }
    if (!remoteEnabled) {
      persist(options.storageKey, options.localValue);
      return Promise.resolve({ accepted: true, duplicate: false, counts: {}, mode: 'local' });
    }
    return request(endpoint, {
      method: 'POST',
      body: JSON.stringify({ topic_id: options.topicId, choice_idx: options.choiceIdx })
    }).then(function (result) {
      persist(options.storageKey, options.localValue);
      result.mode = 'remote';
      return result;
    });
  }

  function getCounts(topicId) {
    if (!remoteEnabled) return Promise.resolve({ counts: {}, mode: 'local' });
    return request(endpoint + '?topic_id=' + encodeURIComponent(topicId), { method: 'GET' })
      .then(function (result) {
        result.mode = 'remote';
        return result;
      });
  }

  function setBusy(container, busy) {
    if (!container) return;
    var buttons = container.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) buttons[i].disabled = busy;
    container.setAttribute('aria-busy', busy ? 'true' : 'false');
  }

  function friendlyError(error) {
    if (error && error.name === 'AbortError') return '投票の送信がタイムアウトしました。通信状況を確認して、もう一度お試しください。';
    if (error && error.status === 403) return 'このページからは投票できません。ページを再読み込みしてください。';
    return '投票を送信できませんでした。通信状況を確認して、もう一度お試しください。';
  }

  function updateStorageNotice() {
    var section = document.getElementById('vote-section');
    if (!section) return;
    var notice = section.querySelector('.vote-storage-note');
    if (!notice) {
      notice = document.createElement('p');
      notice.className = 'vote-storage-note';
      notice.style.cssText = 'font-size:11px;color:var(--muted);margin:10px 0 0;';
      var result = section.querySelector('#vote-result');
      section.insertBefore(notice, result || null);
    }
    notice.textContent = remoteEnabled
      ? '※ 世論調査ではありません。投票内容と、24時間の重複防止用に一方向変換した接続元情報をサーバーに保存します。'
      : '※ 世論調査ではありません。現在、回答はこのブラウザにのみ保存され、サーバーには送信されません。';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', updateStorageNotice, { once: true });
  } else {
    updateStorageNotice();
  }

  window.VoteStore = Object.freeze({
    cast: cast,
    clear: function (storageKey) { localStorage.removeItem(storageKey); },
    getCounts: getCounts,
    getSaved: parseSaved,
    isRemote: function () { return remoteEnabled; },
    setBusy: setBusy,
    friendlyError: friendlyError
  });
})(window);
