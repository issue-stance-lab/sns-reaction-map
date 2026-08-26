# Claude Code セルフレビュー — 2026-06-24

レビュアー: Claude Code（セルフレビュー — 他AIによるクロスレビュー推奨）

## 対象成果物

| ファイル | 内容 |
|---------|------|
| `scripts/run_pipeline.py` (新規・665行) | ワンコマンドパイプライン |

## 総合評価: ⭐⭐⭐⭐☆

スコープの4項目をすべてカバーしており、実用的な品質。いくつかの改善点とリスクあり。

---

## 良い点

- **ワンコマンド化の達成**: fetch→分類→ビルド→ポータル更新の全ステップを `--topic` 1つで実行可能
- **柔軟なステップ制御**: `--skip-fetch`, `--skip-classify`, `--skip-build`, `--skip-portal` で任意ステップをスキップ可能
- **scaffold機能**: `--scaffold --title "タイトル" --template regulation` で5種類のテンプレートからconfig雛形を自動生成。新トピック追加の敷居が大幅に下がる
- **--judge（事前判定）**: 少量サンプルで分類適性をスコアリングし、NG/HOLD/GOで判定。無駄な全量取得を防止
- **--reclassify**: 保留投稿の再分類を専用フラグで実行可能
- **前提チェック**: Node.js、Ollama、設定ファイルの存在を事前に検証
- **--dry-run**: 全ステップを実行せずにコマンドだけ確認可能
- **Step 5 分類診断**: 分類率と評価を自動表示。AI_HANDOFF.mdの基準と連動
- **YAMLパーサのフォールバック**: PyYAMLがなくても正規表現で最低限パース可能

---

## 要修正（必須）

### 1. SUPABASE環境変数がパイプライン経由で渡らない

`build_reaction_map.py` は `os.environ.get("SUPABASE_URL")` で環境変数を読むが、`run_pipeline.py` の `step_build()` は `subprocess.run()` でビルドスクリプトを呼んでいる。

`subprocess.run()` はデフォルトで親プロセスの環境変数を継承するため**動作はする**が、明示的な記述がなく、ユーザーが混乱する可能性がある。

**対応**: `step_build()` にコメントか、`--dry-run` 出力で「SUPABASE_URL/SUPABASE_ANON_KEYが設定されていれば投票機能有効」と表示する。

### 2. `step_reclassify` が入力と出力に同じファイルを指定（541-542行）

```python
"--input", str(classified_file),
"--output", str(classified_file),  # ← 同じファイル
```

`classify_unified.py` がインプレース上書きに対応していれば問題ないが、処理途中でクラッシュするとデータが消失する。

**対応**: 一時ファイルに出力 → 成功したら置換、またはバックアップを自動作成。

---

## 改善提案（任意）

### 3. `load_yaml` のフォールバックパーサが限定的（77-102行）

ネストした辞書・配列の配列・複数行文字列（`|` ブロック）は未対応。現状のYAML構造では動くが、`classification_rules: |` の複数行テキストはパースされない。

**リスク**: PyYAMLがない環境で `classify_unified.py` に `classification_rules` が渡らず分類が壊れる可能性。

**対応案**: `requirements.txt` か pyproject.toml に PyYAML を依存として明記し、フォールバック依存を減らす。

### 4. judge用一時ファイルのクリーンアップ漏れ（521-522行）

`step_judge()` の正常終了時は `tmp_output.unlink()` しているが、`fetch_cmd` が失敗して `rc != 0` の場合、一時ファイルが残る可能性がある（存在チェック前にreturnするため）。

```python
if rc != 0 or dry_run:
    return "GO" if dry_run else "ERR"
# ↑ ここで return されると unlink に到達しない
```

**対応**: `finally` ブロックで確実に削除。

### 5. エラー時のリカバリー情報が少ない

各ステップの失敗時、`run_cmd` は exit code しか表示しない。特に `step_classify` の失敗時、Ollamaのエラー詳細（モデル不在、メモリ不足等）がユーザーに伝わりにくい。

**対応案**: `subprocess.run` に `capture_output=True` を追加し、stderr を表示する。

### 6. `step_stats` の分類率基準がAI_HANDOFF.mdと微妙にずれている

AI_HANDOFF.mdでは:
- 30%以上: ◎ 勢力図として十分成立
- 15-30%: ○ 最低限の勢力図は成立

`step_stats()` では:
- 60%以上: ◎
- 30-59%: ○
- 10-29%: △

基準がより厳しくなっている。意図的なら良いが、AI_HANDOFF.md側も更新すべき。

---

## 他AIへのクロスレビュー依頼

セルフレビューには限界があるため、以下の観点で他AIにクロスレビューを推奨:

- **Codex**: `subprocess.run` のエラーハンドリング、エッジケース
- **Antigravity2**: Supabase連携とパイプラインの統合テスト
- **Hermes**: `--scaffold` で生成されるconfig雛形のUI/UX適合性

---

## チェックリスト

- [ ] `step_reclassify` の同一ファイル入出力のリスク対応（バックアップ or 一時ファイル）
- [ ] Supabase環境変数の案内を `--dry-run` 出力に追加
- [ ] judge一時ファイルの `finally` クリーンアップ
- [ ] PyYAMLを依存として明記
- [ ] AI_HANDOFF.md と `step_stats` の分類率基準を統一

---

## Codex クロスレビュー追記 — 2026-06-24

レビュアー: Codex

### 総合評価

ワンコマンド化の方向性は良いが、現状は「Claude Code のローカル環境では動く」段階に寄っている。運用パイプラインとして他環境・再実行・部分失敗に耐えるには、以下を優先して対応する必要がある。

### 要対応（優先度順）

#### 1. [P1] fetch が Codex 個人環境に固定されており、ワンコマンド再現性がない

対象: `scripts/fetch_yahoo_realtime_node.mjs:8`

```js
const runtimeModules = "/Users/studio/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { chromium } = require(path.join(runtimeModules, "playwright"));
```

`playwright` の読み込み先が個人環境の絶対パスに固定されている。別マシン、CI、通常の clone 環境では `scripts/run_pipeline.py` の fetch 段階で失敗する。

**対応案**:
- リポジトリ直下に `package.json` を追加し、`playwright` を依存として管理する
- `fetch_yahoo_realtime_node.mjs` は通常の依存解決に寄せる

```js
import { chromium } from "playwright";
```

#### 2. [P1] 通常パイプラインが分類の部分失敗で後段ビルドまで進まない

対象:
- `scripts/classify_unified.py:592-616`
- `scripts/run_pipeline.py:638-642`

`classify_unified.py` はバッチ失敗時にフォールバック分類を作り、JSON を保存する。一方で `errors > 0` の場合は exit 2 を返すため、`run_pipeline.py` がそこで停止し、HTML生成・ポータル更新・統計表示に進まない。

Ollama は部分失敗が起きやすい前提なので、運用ワンコマンドとしては過敏に止まりすぎる。

**対応案**:
- フォールバック JSON が保存できた場合は警告扱いで後段へ進む
- もしくは `--strict-classify` のような明示フラグ時のみ exit 2 で停止する
- 最低でも `run_pipeline.py` 側で exit 2 を「部分失敗」として扱い、ユーザーに警告してビルドを継続できるようにする

#### 3. [P2] `--reclassify` が元ファイルを同一パスに上書きする

対象: `scripts/run_pipeline.py:538-546`

```python
"--input", str(classified_file),
"--output", str(classified_file),
```

現状の `classify_unified.py` は入力を読み切ってから保存するため即時破壊ではないが、実行中断・保存失敗・分類ロジック不具合で元分類を失うリスクがある。

**対応案**:
- `*_classified.reclassify.tmp.json` に出力
- 成功時だけ `Path.replace()` で置換
- 置換前に `.bak` を作る

#### 4. [P2] PyYAML 依存が明記されていない

対象:
- `scripts/run_pipeline.py:71-102`
- `scripts/classify_unified.py:36-52`

リポジトリ直下に `requirements.txt` / `pyproject.toml` がない。`run_pipeline.py` には簡易 YAML パーサがあるが、`classify_unified.py` は PyYAML 未導入時に明示的に落ちる。

**対応案**:
- `requirements.txt` を追加し、少なくとも `PyYAML` を明記する
- README / AI_HANDOFF にセットアップ手順を追加する
- `run_pipeline.py` 側の簡易パーサは、依存不足時の案内用途に限定する

#### 5. [P2] 分類率の判定基準が AI_HANDOFF.md と食い違っている

対象:
- `scripts/run_pipeline.py:255-260`
- `AI_HANDOFF.md` の「分類率の目安と解釈」

`AI_HANDOFF.md` は 30%以上を「◎」、15〜30%を「○」としている。一方 `step_stats()` は 60%以上を「◎」、30〜59%を「○」、10〜29%を「△」としており、運用判断がズレる。

**対応案**:
- どちらかの基準に統一する
- 「分類済み率」と「賛成+反対の割合」が別指標なら、名称を分けて表示する

#### 6. [P3] judge の一時ファイルが失敗時に残る

対象: `scripts/run_pipeline.py:488-522`

`step_judge()` は fetch 失敗時や JSON パース失敗時に `tmp_output.unlink()` へ到達しない。

**対応案**:
- `try/finally` で `tmp_output` を削除する

### セルフレビューへの補足

- Supabase 環境変数は `subprocess.run()` が親環境を継承するため、「渡らない」問題ではない。説明不足として扱えばよい。
- ただし `--dry-run` や完了ログで `SUPABASE_URL` / `SUPABASE_ANON_KEY` の有無を案内する改善は有用。

### Codexチェックリスト

- [ ] `fetch_yahoo_realtime_node.mjs` の Codex 絶対パス依存を除去
- [ ] `package.json` などで Node 依存を明記
- [ ] `classify_unified.py` の部分失敗時 exit code と `run_pipeline.py` の停止条件を見直す
- [ ] `--reclassify` を一時ファイル + 成功時置換に変更
- [ ] Python 依存ファイルに `PyYAML` を明記
- [ ] `step_stats()` と `AI_HANDOFF.md` の分類率基準を統一
- [x] `step_judge()` の一時ファイル削除を `finally` 化

---

## Codex 再レビュー追記 — 2026-06-24

レビュアー: Codex

### 結論

前回の重大指摘（P1）は概ね解消済み。残件は `step_judge()` の一時ファイル削除漏れのみ。

### 対応確認済み

- [x] `fetch_yahoo_realtime_node.mjs` の Codex 絶対パス依存を除去
- [x] `package.json` / `package-lock.json` / `.gitignore` に Node 依存管理を追加
- [x] `playwright` を通常 import に変更
- [x] 分類の部分失敗時（exit 2）に、出力JSONがあれば警告扱いで後段ビルドへ続行
- [x] `--reclassify` を一時ファイル出力 + `.bak` バックアップ + 成功時置換方式に変更
- [x] `requirements.txt` に `PyYAML` を明記
- [x] `AI_HANDOFF.md` と `step_stats()` の分類率説明を、別指標として明確化

### 残件

#### [P3] `step_judge()` の一時ファイル削除が fetch 失敗時にまだ漏れる

対象: `scripts/run_pipeline.py:486-488`

```python
rc = run_cmd(fetch_cmd, dry_run=dry_run, label="判定用サンプル取得中...")
if rc != 0 or dry_run:
    return "GO" if dry_run else "ERR"
```

この早期 return は `finally` の外にある。fetch が途中まで `social-samples/{slug}_judge_sample.json` を作ってから失敗した場合、一時ファイルが残る。

**対応案**:
- `rc = run_cmd(...)` から judge 実行まで全体を `try/finally` に入れる
- `dry_run` 時はファイルが作られない想定だが、同じ `finally` に含めて問題ない

### 検証結果

- `python3 -m py_compile scripts/run_pipeline.py scripts/classify_unified.py scripts/trend_judge.py` 成功
- `node --check scripts/fetch_yahoo_realtime_node.mjs` 成功
- `import('playwright')` 成功
