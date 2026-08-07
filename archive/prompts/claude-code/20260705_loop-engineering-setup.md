# ループエンジニアリング体制のセットアップ

## あなたの役割

あなたは「SNS反応まっぷ」プロジェクトのハブAI（Claude Code）です。このセッションでは、これまで課題番号ベース（課題1〜28）で場当たり的に進んできた管理体制を、**テーマ台帳 + 定常ループ**の体制に移行します。

- リポジトリ: issue-stance-aggregator
- プロジェクト概要: AI_HANDOFF.md
- 旧管理台帳: TASK_BOARD.md（読み込むこと。ただし今後は縮小する）

## 背景（なぜ移行するか）

現状の問題:
- 管理の主キーが「課題番号」だが、実作業は「テーマ×工程」で発生する
- 1テーマの現状を知るのに複数の課題セクションを横断して読む必要がある
- 修正のたびに課題番号が増え、完了課題も残るため台帳が肥大化
- 「管理・修正・補充・追加」が別々の課題として扱われ、一体的に回らない

## 移行後の体制

### 1. テーマ台帳 `THEMES.yaml`（リポジトリ直下に新規作成）

テーマを主キーとする単一の真実源。各テーマの工程状態を機械可読で持つ。

```yaml
# 工程の定義（全テーマ共通のステートマシン）
# collect:   Yahoo検索でデータ収集済み
# classify:  Ollama分類済み（1D）
# classify2d: 2D分類済み（エラー率10%以下）
# page_v3:   v3フォーマットのHTMLが公開されている
# manga_data: 漫画データ・プロンプト作成済み
# manga_img:  画像生成・HTML反映済み（画像生成は人間の手動作業）
# published: ポータル掲載・sitemap登録済み
# 各工程の値: done / partial / todo / blocked / n-a
# refresh_at: 次回データ補充の目安日（補充は繰り返し工程）

themes:
  ai-copyright:
    title: 生成AIと著作権
    html: docs/ai-copyright-reaction-map.html
    collect: done
    classify: done
    classify2d: done
    page_v3: done
    manga_data: done
    manga_img: done
    published: done
    refresh_at: 2026-07-12
    notes: v3試験実装テーマ。canvas IDは正典（smCanvasMain/smCanvasHeat）
  # ... 残り7テーマも同様に
```

**初回タスク**: TASK_BOARD.md の課題7/9/21/23/24/25/26/27/28 の記述と実ファイル（docs/*.html、social-samples/、manga-prompts/、configs/topics/）を突き合わせ、8テーマ全部の正確な状態を調査して THEMES.yaml を作成すること。**記述を信じず、実ファイルを確認して判定する**（例: HTMLに smCanvasMain があるか、manga-prompts/ にファイルがあるか、2D分類JSONのエラー率はいくつか）。

既知の状態（前セッションからの引き継ぎ、要実地検証）:
- v3完了5テーマ: ai-copyright / bike-blue-ticket / bukatsu-chiiki / constitutional-amendment / elderly-license-revocation
- 旧形式3テーマ（アーカイブ中）: takaichi / henoko-student-accident / school-nickname-ban
- bukatsu-chiiki は漫画画像が未生成（テキストカード代替中、旧課題27）
- school の2D分類は70%エラーで再実行待ち、henoko/takaichi は2D軸設計から（旧課題28）
- リポジトリ直下に `social-samples/*_2d_classified.test.json` が5テーマ分untrackedで存在する。誰が作ったか不明なので、内容・件数・エラー率を検分して採用可否を判断すること

### 2. TASK_BOARD.md の縮小

テーマ個別の工程管理を THEMES.yaml へ移し、TASK_BOARD.md は**テーマ横断の課題だけ**残す:
- 集客（X運用・SEO）/ 収益化（AdSense）/ パイプライン改善 / アカウント管理
- 完了済み課題は `docs/` 外の `archive/TASK_BOARD_ARCHIVE.md` へ移動
- 冒頭に「テーマ個別の状態は THEMES.yaml を見よ」と明記

### 3. ハブの定常ループ `LOOP.md`（リポジトリ直下に新規作成）

ハブが毎セッション実行する手順書。内容:

```
① 監査: THEMES.yaml と実ファイルを突き合わせ、ズレがあれば台帳を直す
② 選定: 次の一手を1つ選ぶ。優先順位ルール:
   1. 公開済みページの破損・バグ（最優先）
   2. blocked の解除（人間への依頼事項を明確にして報告）
   3. 未完テーマの次工程を1つ進める（完成に近いテーマから）
   4. refresh_at を過ぎたテーマのデータ補充
   5. 新テーマの追加(2日に1本ペース、全テーマがdoneに近いときのみ)
③ 発注: configs/prompts/ にワーカープロンプトを生成。命名:
   {YYYYMMDD}_{theme}-{工程}.md。共通の制約(GA4/AdSense/OGP/Supabase保持、
   ブランチ task/{theme}-{工程}、座標対応表は自テーマで導出)を必ず含める
④ 検証: ワーカー報告後、ハブがブラウザ検証(コンソールエラー・375px・保護タグgrep)
⑤ 統合: mainへマージ、THEMES.yaml 更新、必要なら人間に手動作業を依頼
⑥ ①へ戻る。1セッションで複数周回してよい
```

人間（オーナー）の役割はプロンプトの受け渡しと画像生成などの手動作業のみ。判断はループが行う。

### 4. ワーカープロンプトの共通テンプレート

`templates/worker-prompt-template.md` を新規作成。既存の良いプロンプト
（configs/prompts/hermes/20260705_task26-phased-portal.md 等）から共通部を抽出:
- コンテキスト（役割・参照ファイル）
- 保護タグ一覧（GA4: G-K10S4YCZFH / AdSense: ca-pub-2542211932832864 / SEO_META / Supabase）
- ブランチ運用
- 完了条件・報告フォーマット（変更サマリー / grep確認結果 / 迷った点）

## このセッションの完了条件

1. THEMES.yaml が実ファイル調査に基づいて作成されている（8テーマ全部）
2. LOOP.md が作成されている
3. templates/worker-prompt-template.md が作成されている
4. TASK_BOARD.md が縮小され、完了課題が archive/ へ移動されている
5. CLAUDE.md の「セッション開始時に読むファイル」を Agent.md + LOOP.md + THEMES.yaml に更新
6. 上記を main にコミット・プッシュ（ブランチ task/loop-engineering-setup 経由）
7. **ループを1周実行してみる**: ②の優先順位ルールで次の一手を選び、ワーカープロンプトを1本生成して人間に渡す（これが体制の動作確認になる）

## 制約

- docs/ 配下の公開HTMLはこのセッションでは変更しない（体制構築に集中）
- 既存の configs/prompts/ 内の過去プロンプトは移動・削除しない（履歴として残す）
- 判断に迷ったら仮定を明記して進める。人間への質問は最後にまとめる
