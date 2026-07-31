import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('../docs/vote-store.js', import.meta.url), 'utf8');

function createRuntime(config, fetchImpl) {
  const values = new Map();
  const localStorage = {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
    removeItem(key) { values.delete(key); },
  };
  const document = {
    readyState: 'loading',
    addEventListener() {},
    getElementById() { return null; },
  };
  const window = { SNS_VOTE_CONFIG: config };
  vm.runInNewContext(source, {
    AbortController,
    clearTimeout,
    console,
    document,
    fetch: fetchImpl,
    localStorage,
    setTimeout,
    window,
  });
  return { store: window.VoteStore, values };
}

test('設定が空ならlocalStorageへ保存する', async () => {
  const runtime = createRuntime({}, async () => { throw new Error('fetch should not run'); });
  const result = await runtime.store.cast({
    topicId: 'topic', choiceIdx: 2, storageKey: 'vote', localValue: { issueIdx: 0, stanceIdx: 2 },
  });
  assert.equal(result.mode, 'local');
  assert.deepEqual(JSON.parse(runtime.values.get('vote')), { issueIdx: 0, stanceIdx: 2 });
});

test('本番設定時はEdge Function成功後にだけ保存する', async () => {
  let captured;
  const runtime = createRuntime(
    { supabaseUrl: 'https://example.supabase.co/', publishableKey: 'sb_publishable_test' },
    async (url, options) => {
      captured = { url, options };
      return { ok: true, status: 200, json: async () => ({ accepted: true, duplicate: false, counts: { 2: 1 } }) };
    },
  );
  const result = await runtime.store.cast({ topicId: 'topic', choiceIdx: 2, storageKey: 'vote', localValue: 2 });
  assert.equal(result.mode, 'remote');
  assert.equal(captured.url, 'https://example.supabase.co/functions/v1/cast-vote');
  assert.equal(captured.options.headers.apikey, 'sb_publishable_test');
  assert.equal(runtime.values.get('vote'), '2');
});

test('送信失敗時は投票済み状態を保存しない', async () => {
  const runtime = createRuntime(
    { supabaseUrl: 'https://example.supabase.co', publishableKey: 'sb_publishable_test' },
    async () => ({ ok: false, status: 500, json: async () => ({ error: 'vote_failed' }) }),
  );
  await assert.rejects(
    runtime.store.cast({ topicId: 'topic', choiceIdx: 1, storageKey: 'vote', localValue: 1 }),
    /vote_failed/,
  );
  assert.equal(runtime.values.has('vote'), false);
});
