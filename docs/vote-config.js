/*
 * 公開用設定。Supabase Dashboard の Connect 画面にある Project URL と
 * Publishable key（または移行期間中のlegacy anon key）だけを設定する。
 * Secret key / Service Role key は絶対にここへ置かない。
 */
window.SNS_VOTE_CONFIG = Object.freeze({
  supabaseUrl: "\"https://qslrlprzoucrlptnhsmi.supabase.co\"",
  publishableKey: "\"sb_publishable_FoQdRPaSTmNJZSAGwy4xJg_HcVOfOhr\""
});
