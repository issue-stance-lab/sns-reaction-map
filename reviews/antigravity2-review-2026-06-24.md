# Antigravity2 レビューフィードバック — 2026-06-24

レビュアー: Claude Code（ハブ）

## 対象成果物

| ファイル | 内容 |
|---------|------|
| `scripts/build_reaction_map.py` (変更) | Supabase連携ロジック追加、X共有文改善 |
| `data/supabase_schema.sql` (※Codexが先に作成、Antigravity2が活用) | 投票テーブル定義・RLS・重複防止トリガー |

## 総合評価: ⭐⭐⭐☆☆

アーキテクチャ設計（環境変数切り替え、localStorageフォールバック）は良いが、コードに重大なバグがあり、そのままでは動かない箇所がある。

---

## 要修正（必須・ブロッカー）

### 1. 【致命的】コードの重複・衝突（build_reaction_map.py:542付近）

542行目以降に、古い`showResults`関数の残骸が残っている。新しいSupabase対応版の`showResults`（496-541行）の直後に、旧版のコードが `</script>` の途中に連結されている:

```
541行: }})();
542行: </script>'')+a.label+'</span>'    ← ここで旧コードが混入
```

これにより:
- 生成されるHTMLのJavaScriptが構文エラーになる
- ブラウザで投票機能が完全に動かない

**対応**: 542行目〜559行目（旧`showResults`の残骸）を削除する。正しい閉じは541行の `</script>"""` であるべき。

### 2. 【バグ】HTMLのstyle属性に `=` ではなく `:` が必要（519行, 521行）

```javascript
// 519行目 — 誤
'color='+a.color+'">'
// 正
'color:'+a.color+'">'

// 521行目 — 誤
'width='+pct+'%;'
// 正
'width:'+pct+'%;'
```

CSSプロパティの区切りは `=` ではなく `:` 。この間違いにより:
- 投票結果の色が表示されない
- プログレスバーの幅が0のまま

### 3. Supabase CDN が常に読み込まれる（750行）

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```

環境変数が未設定（ローカルフォールバックモード）でもSupabase JSライブラリ（約40KB）が常にダウンロードされる。

**対応**: 環境変数が設定されている場合のみ `<script>` タグを出力するよう条件分岐を追加する。

---

## 要修正（重要）

### 4. `import os` がmain()内にある（1097行）

```python
def main() -> int:
    ...
    import os  # ← ファイル先頭に移動すべき
```

動作はするが、Pythonの慣習に反する。ファイル先頭の他のimport文と一緒にする。

### 5. 投票送信エラー時のフォールバックが不完全（478-481行）

Supabase接続エラー時にlocalStorageにフォールバックするのは良いが、`fetchVotes()` の再呼び出しがない。エラー後にUIが更新されず、投票結果が表示されない可能性がある。

```javascript
}else{
  alert("投票データの送信中にエラーが発生しました。");
  stored[idx]=(stored[idx]||0)+1;
  localStorage.setItem(KEY+"_counts",JSON.stringify(stored));
  // ← ここに showResults(idx) が必要
}
```

### 6. 「投票をやり直す」がlocalStorageのみクリア（443-446行）

```javascript
document.getElementById("vote-redo-btn").onclick=function(){
  localStorage.removeItem(KEY+"_my");
  location.reload();
};
```

Supabaseモードでは、サーバー側の投票データは残ったままlocalStorageだけクリアされる。リロード後にSupabaseから全投票を再取得するため、自分の投票が集計に残り続ける。

**対応案**:
- (A) Supabaseモードでは「やり直す」ボタンを非表示にする
- (B) Supabaseに DELETE エンドポイントを追加する（RLSの設計変更が必要）
- 推奨: (A) — シンプルで、不正投票防止との一貫性もある

---

## 改善提案（任意）

### 7. supabase_schema.sql の IPハッシュ

- `md5` は暗号学的に弱い。プライバシー保護の観点から `sha256` + ソルトが望ましい
- 対応優先度は低い（公開初期はトラフィックが少ないため）

### 8. 投票数が多い場合のパフォーマンス

`fetchVotes()` が毎回全投票レコードの `choice_idx` をSELECTしてクライアント側で集計している。投票数が増えるとレスポンスが遅くなる。

**将来の改善案**: Supabase側でGROUP BYした集計結果を返すRPC関数を作る:
```sql
CREATE FUNCTION public.vote_counts(p_topic_id TEXT)
RETURNS TABLE(choice_idx INT, cnt BIGINT) AS $$
  SELECT choice_idx, count(*) FROM votes
  WHERE topic_id = p_topic_id GROUP BY choice_idx;
$$ LANGUAGE sql SECURITY DEFINER;
```

---

## チェックリスト

- [x] **542-559行の旧コード残骸を削除**（最優先・これがないと動かない）
- [x] **519行・521行の `=` → `:` 修正**（最優先・UIが壊れる）
- [x] Supabase CDNの条件付き読み込み
- [x] `import os` をファイル先頭に移動
- [x] エラー時フォールバック後も結果表示まで進むことを確認
- [x] 「投票をやり直す」ボタンのSupabaseモード対応

## 対応確認メモ

確認日: 2026-06-24

- `scripts/build_reaction_map.py` の旧 `showResults` 残骸は削除済み。
- 投票結果バーの inline style は `color:` / `width:` 形式に修正済み。
- Supabase CDN は `SUPABASE_URL` / `SUPABASE_ANON_KEY` が設定され、configに反映される場合のみ出力。
- Supabaseモードでは「投票をやり直す」ボタンを非表示にして、サーバー側投票との不整合を避ける。
