# 品質監査: 課題77 Part B（案2）「授業・ディベートで使うとき」の節

- 監査日: 2026-09-21
- 対象: 作業ツリー `isa-wt-growth-cite-search-b`（ブランチ `task/growth-cite-and-search-structure-b`、分岐元 42f6db8）の未コミットの変更。
  新規 `scripts/seo/apply_classroom_section.py`・`configs/classroom/{theme}.json`（10件）・`tests/test_classroom_section.py`、
  共有 CSS/JS（`.classroom-*`、印刷、`hashchange`）、`refresh_topic.py`・`verify_builder_rebuildability.py` への配線、公開10ページ
- 監査者: 発注書を書いたセッション（実装したセッションとは別）
- 判定: **needs_revision（直す箇所は1つ）**。375px で一次資料のリンク文字が画面外に切れる。直して再確認したら ready_for_ceo にしてよい

## 直すこと（1件）

**375px で「確かめる一次資料」のリンクが右に切れる。** `docs/topic-modern.css` の
`.classroom-reasons a, .classroom-sources a { white-space: nowrap }` のため、長い資料名（例: 副首都の法律名 64文字）が
折り返されず 818px まで伸びる。ページ全体は `overflow-x: clip` なので横スクロールは起きないが、**文字は見えないまま切れる**
（実測: リンク右端 818px、列幅 317px。10テーマ中、資料名が25文字を超えるものはほぼ全テーマにある）。
実装側の「375pxで横スクロールなし」の確認は `documentElement.scrollWidth` だけを見ており、この切れ方は検出できていない。

- 直し方: `.classroom-sources a` の `white-space: nowrap` を外す（`overflow-wrap: anywhere` を足すとより安全）。
  「→ 論点「…」を見る」のリンクも長い論点名では同じことが起きうるので、同様に折り返しを許す
- 直したら: `TOPIC_CSS_VERSION` を 31 に上げて10ページを再適用し、375px で `.classroom-section` 内の全 `a` の right が 375 以下であることを確認する。
  `tests/test_classroom_section.py` に「CSS に `.classroom-sources a` の nowrap が無い」程度の固定を足すと再発しない

## 判定の根拠

### 自動検査（作業ツリーで実行）

| 検査 | 結果 |
|---|---|
| `python3 -m unittest discover -s tests` | OK（新規 13件を含む） |
| `python3 scripts/run_public_checks.py` | OK |
| `python3 scripts/verify_theme_page.py` | 11テーマ NG 0件（builder rebuildability の「教室節の2回目 changed=0」を含む） |
| `python3 scripts/verify_number_provenance.py` | NG 0件（節に新しい数字を書いていない） |
| `python3 scripts/verify_page_originality.py` | OK（固定見出し・使い方文は `configs/page-originality.json` の allow に理由付きで登録） |
| `python3 scripts/verify_ai_tone.py` | 問題なし（ペルソナ復元済みで実行） |
| `python3 scripts/seo/validate_theme_seo.py` | OK |
| `python3 scripts/seo/apply_classroom_section.py` を再実行 | changed=0（同じ入力で差分ゼロ） |
| 一次資料リンク 30本 | すべて HTTP 200（curl で確認） |

### 実機確認（作業ツリーの `docs/` を 127.0.0.1 で配信、副首都で確認）

- 節は `<main>` 内、投票セクションの直後・「このページの作り方」（`ARTICLE_TRUST_START`）の直前にある（10ページとも同じ位置。生成AI著作権のみ論点カードの直後）
- 見出し「授業・ディベートで使うとき」→「法案賛成・推進」側／「法案反対」側の理由3つずつ（各理由に論点への内部リンク）→ 確かめる一次資料3件 → 問いの例3件 → 使い方＋「この節を印刷する」
- 内部リンクを押すと `hashchange` で論点が切り替わる（Part A 監査の推奨修正が入っている）。GA4 に `classroom_link_click {theme_id, issue_id}`、印刷ボタンで `classroom_print` が送られる。コンソールエラーなし
- 1280px: 賛成・反対が左右2列（557px×2）、資料・問い・使い方が下に並ぶ。要素のはみ出しなし
- 375px: 1列に折りたたまれ、印刷ボタンは使い方の下に回る。**ただし上記のとおり一次資料のリンク文字が切れる**
- 印刷（A4 1枚）: 自動化ツールでは印刷プレビューを開けず未確認。CSS は「節以外を非表示にして節を先頭に絶対配置」の定番の型で、文法上の問題はない。公開前にオーナーがブラウザの印刷プレビューで1テーマ見ておくとよい

### 中身（10テーマの `configs/classroom/*.json` を通読）

- 賛成・反対の理由は各テーマ固有で、テーマ間の使い回しなし（テストでも固定）。理由の末尾は必ず論点への内部リンクで、リンク先アンカーは全ページ実在
- 立場の呼び方は公開JSONの立場ラベルに沿っている（例: 副首都「法案賛成・推進」「法案反対」、部活動「移行支持」「慎重・反対」）
- 問いは「〜すべきか」の形で、一方の立場を前提にしていない
- 一次資料は法令（e-Gov）・国会会議録・官庁資料・自治体資料で、各テーマの一次資料メモの範囲内
- 数字は条番号・年月などに限られ、割合や件数は書いていない
- 文体がテーマによって「だ・である」と「です・ます」に分かれている（憲法改正・辺野古・あだ名は「です・ます」）。読者には各ページ内で完結するので実害は小さいが、揃えるなら「だ・である」に寄せると他の節と合う（任意）
- 辺野古（高校生死亡事故）は授業題材として扱う配慮が要るテーマだが、問いは学校の安全管理の義務・国の関与の範囲・報道の表現に限られ、亡くなった生徒個人や遺族に触れていない。公開品質ゲートの「事故・遺族への配慮」は満たしている
- 発注書との相違: 冪等検査の配線先を `verify_theme_page.py` ではなく `verify_builder_rebuildability.py` にした点は、実体がそちらだったためで妥当

### 発注書 B-1〜B-5 との突き合わせ

- B-1 置き場と方式: 共有ブロック・相手のマーカー直前・共通スクリプト・昇格列2箇所と冪等検査への配線、いずれも満たす
- B-2 中身: 理由3+3・一次資料3・問い3・使い方・印刷（PDF は作っていない）・GA4 2イベント、満たす
- B-3 文章の決まり: AI臭検査・使い回し検査・行動原則、満たす
- B-4 公開前: この監査。CEO承認と release スキルはこれから
- B-5 完了条件: 375px の項目だけ未達（上記）

## 残るリスク

- 印刷プレビューは未確認（上記）
- 節は10ページ全部で同じ形なので、AdSense の「定型的な繰り返し」の見方に触れる可能性がゼロではない。理由・資料・問いが全テーマ固有である点で、既存の「このページの作り方」節と同じ扱いになると考える

## 戻し方

- マージ後に問題が出たら、`configs/classroom/` と `apply_classroom_section.py` を残したまま、`refresh_topic.py`・`verify_builder_rebuildability.py` の配線を外し、
  各ページの `<!-- CLASSROOM_START -->`〜`<!-- CLASSROOM_END -->` を削って `TOPIC_CSS_VERSION` を上げる。または該当マージを `git revert`
