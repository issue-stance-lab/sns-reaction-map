# GROWTH_LOOP.md — グロースループ手順書

目的: 来訪者増加・回遊率改善・投票数増加・SNSシェア増加。
台帳: `GROWTH.yaml`。制作・品質維持は `LOOP.md` / `THEMES.yaml` の管轄で、本ループでは扱わない。

---

## フェーズ定義

GROWTH.yaml の `phase.current` を確認してから以下を適用する。

### 初期トラクションフェーズ（phase: initial_traction）

`phase.until` の全条件（Xフォロワー100・weekly_users100・votes_total100）を満たすまで継続。

**日次ゴール: 露出（X）か体験（サイト改善）のどちらかを必ず前に進める。**

- **judge_at は振り返り日**。母数が少なく統計的因果判定は不可能。adopted/rejected を急がず「何が反応を得たか」の観察を優先する。超過した measuring 実験は `reflection` フィールドに観察ログを書いて期限延長してよい（観察のない延長は塩漬け扱い）
- **x-posting は毎ループ必須。** ② 選定の最優先に格上げする（judge_at 判定より先に確認）
- **KPIの上下より活動量と反応の有無を見る**: 反応があった投稿・テーマ・導線を翌週増やす。反応がないものは文言・切り口を変えて再試行する
- **計測中でも以下は止めない**: X投稿/リプライ、プロフィール改善、ページ読みやすさ・モバイルUX・投票導線・OGP/タイトルの改善、明らかな不具合修正。何を変えたかは GROWTH.yaml `activity_log` に記録する

### 成長フェーズへの卒業

until 条件をすべて達成した週の月曜に `phase.current: growth`・`graduated_on: YYYY-MM-DD` を更新する。以降は judge_at を通常の判定期限（adopted/rejected 必須）として扱う。

---

## 制作ループとの関係（最重要ルール）

1. **制作ループが常に優先。** 公開済みページの破損・バグがある間、グロースループは起動しない。
2. **同じセッションで両ループを回してよい**が、順序は必ず 制作ループ①監査 → 問題なし → グロースループ。
3. グロース施策も保護タグ（GA4 / AdSense / Supabase / OGP）を絶対に壊さない。検証手順は LOOP.md ④と同一。
4. ブランチ: `task/growth-{id}`（例: `task/growth-share-after-vote`）。main直接コミット禁止。
5. `measuring` 状態の実験があるときは、計測対象ページへの他のグロース変更を保留する（効果の切り分けのため）。

## ① 計測

GROWTH.yaml の kpi.snapshots を確認する。

- **日付確認**: ループ開始時に必ず現在日付・曜日・タイムゾーンを確認する（例: `date '+%Y-%m-%d %A %Z'`）。相対日付で判断しない。
- **自動KPI取得**: 原則として毎回 `python3 scripts/fetch_growth_kpi.py` を実行し、GA4 / Search Console / Supabase の最新値を確認する。
  - 毎日回す場合、`GROWTH.yaml` への追記は**週1回（月曜推奨）**、または施策判定日・大きな変化があった日のみでよい。
  - 月曜以外の通常周回では、取得結果を見て異常検知・施策選定に使い、必要がなければ `GROWTH.yaml` へ追記しない。
  - 自動取得が失敗した場合のみ、人間に数値取得を依頼する。
- 最新スナップショットが7日以上古い → `python3 scripts/fetch_growth_kpi.py` の出力を `GROWTH.yaml` に追記する（自動取得失敗時のみ人間へ依頼）
- judge_at を過ぎた measuring 実験がある → **フェーズに応じて扱いが異なる**
  - 初期トラクションフェーズ: adopted/rejected を急がず、`reflection` フィールドに観察ログを書いて延長。観察なき延長は塩漬け扱い
  - 成長フェーズ: **判定を最優先**。adopted / rejected に倒し、result に根拠を書く
- ベースラインが一度も取れていない場合でも、capabilities の実装は先行してよい（計測基盤より導線が先）

## ② 選定

次の一手を**1つ**選ぶ。

**初期トラクションフェーズ中の優先順位（通常フェーズとは異なる）:**

1. **x-posting の今日の行動を決める**（毎ループ必須。何をするか決めてから他の選定に進む）
2. **x-profile の週次見直し**（last_run が7日以上古い場合）
3. **judge_at 超過の measuring 実験への reflection 記録**（adopted/rejected は急がない。GROWTH.yaml の当該実験に `reflection` フィールドで観察ログを書く）
4. **recurring の期限超過**（x-posting / x-profile 以外）
5. **capabilities の priority 順に次の1つを進める**
6. **experiments の起票・開始**
7. **新しい仮説の起票**

**成長フェーズ中の優先順位（通常）:**

1. **judge_at 超過の実験の判定**（adopted / rejected に倒す）
2. **recurring の期限超過**
3. **capabilities の priority 順に次の1つを進める**（idea → building → built → measure → done）
4. **experiments の起票・開始**（measuring が0のときのみ開始可）
5. **新しい仮説の起票**

## ③ 実装・発注

- 小さな変更（文言、リンク追加）はハブが直接ブランチを切って実装してよい
- 規模が大きいもの（投票完了画面の改修など）は LOOP.md ③と同様に `configs/prompts/` へワーカープロンプトを発注
  - 命名: `{YYYYMMDD}_growth-{id}.md`
  - LOOP.md ③の共通制約（保護タグ・ブランチ規則）を必ず含める
- 計測可能にする: 新しい導線には GA4 イベントまたは utm パラメータを必ず付ける。**計測できない施策は実装しない**

## ④ 検証

LOOP.md ④と同一（コンソールエラーなし / 375px横スクロールなし / 保護タグgrep）。
加えて: 追加した GA4 イベント・utm がネットワークタブで発火することを確認。

## ⑤ 統合・記録

- main へマージ
- GROWTH.yaml の status を更新（building → measuring なら started_at と judge_at を必ず記入。目安2週間後）
- 人間への依頼事項（投稿・管理画面確認・数値取得）を明示して報告

## ⑥ ループ

①へ戻る。1セッションで複数周回してよいが、**実装を伴う施策は1セッション1つまで**。

---

## 判定基準の目安

- adopted: 対象指標がベースライン比で改善傾向、かつ他指標の悪化なし
- rejected: 2週間で有意な変化なし、または直帰率等の悪化。**rejected も学びとして result に残す**（消さない）
- データ不足で判定不能: judge_at を1回だけ延長可。2回目は rejected 扱い

## 人間（オーナー）の役割

- GA4 / Search Console / Supabase の数値取得は通常不要（`scripts/fetch_growth_kpi.py` で自動取得）。OAuth期限切れ・権限エラーなど自動取得が失敗したときだけ対応する
- X の実投稿・リプライ操作
- AdSense 等、管理画面での操作
- adopted / rejected の最終承認（ハブが判定案を出し、人間が承認）

判断はループが行う。人間は実行と数値提供のみ。
