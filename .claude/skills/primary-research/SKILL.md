---
name: primary-research
description: 各テーマの一次資料メモ（quality/research/*-primary-sources.md）を定期的に再調査・更新するための手順。「一次資料を更新して」「◯◯テーマの一次資料を見直して」「管理ダッシュボードが一次資料の再確認遅れを出している」といった作業ではこのスキルを読むこと。FACT_CHECK_GUIDE.mdの「投稿の主張を一次資料と突き合わせる」セクションをページに実装する前提の調査であり、ページへの反映自体は別作業（TASK_BOARD.md 課題58参照）。
---

# 一次資料メモの定期更新

## この作業の位置づけ

`quality/research/{テーマ}-primary-sources.md` は、法改正・統計・裁判例などの一次資料
（省庁・国会会議録・e-Gov・自治体・政党の公表資料のみ。民間シンクタンク・事業者団体・
まとめブログは不採用）を集めた調査メモ。ページ（`docs/*.html`）に直接載せるものではなく、
FACT_CHECK_GUIDE.md の実装工程の土台になる下調べ。

法律は改正され、統計は更新される。**一度作った一次資料メモは古くなる。**
このスキルは「古くなったことに気づかず放置される」事故を防ぐための、期日駆動の定例作業。
`LOOP.md` のような自律周回は敗れた運用（`OPERATIONS.md` 冒頭）なので、代わりに
`scripts/build_admin_dashboard.py` が遅れを検知する方式に乗せる。

## 遅れの検知の仕組み

`quality/research/status.yaml` にテーマごとの最終確認日を記録する。

```yaml
default_review_days: 90   # 既定の再確認サイクル（日数）
themes:
  ai-copyright:
    last_verified: "2026-08-31"
    note: "21本の一次資料を確認済み。次は文化庁ガイドラインの改訂有無を見る"
  koshitsu-tenpakai:
    last_verified: "2026-08-31"
    review_days: 30        # 敏感なテーマは既定より短くできる
    note: "改正法(令和8年法律66号)の施行が2026-10-24頃。施行後に附則本文を確認する"
```

`scripts/admin_dashboard/collect.py` の `collect_primary_research()` がこのファイルを読み、
`review_days`（無ければ `default_review_days`）を過ぎたテーマを
`python3 scripts/build_admin_dashboard.py` の「1. 今日の次の一手」「遅れ・問題」に出す。

**このファイルを更新しない限り、いくら調査しても「遅れなし」にはならない。**
調査した直後に `last_verified` を今日の日付へ書き換えること（`OPERATIONS.md` の
「台帳を更新するのは誰か」と同じ原則＝作業したセッションがその場で更新する）。

## 1テーマを再確認する手順

1. **専用worktreeを作る**（`OPERATIONS.md` ⓪）。研究メモ自体は非公開の正典を含まないため
   `tar` 復元は不要。ただし共有ツリーで直接作業しない
   ```sh
   git worktree add ../isa-wt-primary-research-{テーマ} -b task/primary-research-{テーマ}
   ```
2. 対象メモ（`quality/research/{テーマ}-primary-sources.md`）を読み、
   「確認できなかったこと」と、法改正・統計更新が起きていそうな箇所を洗い出す
3. 一次資料の定義を厳密に守って調べる（省庁・国会会議録・e-Gov・自治体・政党の公表資料のみ）。
   例外的に業界団体等の「その団体自身の規則」を採用する場合は、オーナーに確認する
   （日本中体連の競技規則を採用した前例あり）
4. **機械的に照合できるものは必ず照合する。** LLMの要約や引用をそのまま信じない
   - 国会発言の引用 → `kokkai.ndl.go.jp` の `/api/speech`（issueIDで発言全文を取得し、
     引用符の中身が原文に実在するか突き合わせる）
   - 法令条文の引用 → `laws.e-gov.go.jp` の `/api/2/law_data/{law_id}` で本文を取得し突き合わせる
   - URLの生存確認 → `curl -sI` で200を確認する
   - 過去に検出された実際の誤り: 会議録名をそのままURLエンコードしただけの捏造ID、
     「だ・である調」への書き換え後に引用符で囲んだ発言、注記文までURLに含めた誤判定
5. メモを更新し、`quality/research/README.md` の状態欄も直す
6. **`quality/research/status.yaml` の `last_verified` を今日の日付に書き換える。**
   忘れると、正しく再確認したのにダッシュボードが遅れ扱いのままになる
7. worktree 内でコミット。ページへの反映が目的でない限り、mainへは
   `quality/research/` と `status.yaml` の変更のみをマージすればよい

## 頻度の目安

- **既定90日。** 一次資料（法令・統計）は大きくは動かないテーマが大半なので、
  週次・月次のような短いサイクルは過剰
- **法改正・審議中の議案があるテーマは短くする**（`review_days` で個別設定）。
  例: 施行日が数か月後に迫っている法律を含むテーマ
- 全10テーマ（takaichiを除く公開中の全テーマ）を毎回まとめて回す必要はない。
  ダッシュボードが「遅れているテーマ」だけを教えるので、それを1つずつ進める
