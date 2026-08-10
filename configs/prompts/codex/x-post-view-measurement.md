# X投稿の表示回数を計測する

@sns_hannou_ma がすでに投稿したリプライ・論点ポスト・会話フォローのうち、
投稿から24時間以上たった未計測分だけを計測し、`x-posts.md` に記録する。

## スコープ

- 投稿後の表示回数計測だけを行う
- 投稿候補探し、X検索、投稿案作成、投稿操作は行わない
- 認証情報を読んだり保存したりしない
- 表の見出しは変更しない
- 数値がすでにある箇所は、暫定値を含めて上書きしない

## 手順

1. `CLAUDE.md` を読む
2. `python3 scripts/x_post_views.py pending --json` を実行する
3. 結果が `[]` なら、変更・テスト・コミットをせず終了する
4. `due` と `overdue` の投稿URLをログイン済みChromeで直接開く
5. URLの投稿IDと一致する @sns_hannou_ma の記事を特定し、その記事内の
   `[role="group"]` の `aria-label` から「表示」を読む
6. 全件取得できた場合だけ、次の1コマンドで書き戻す

```bash
python3 scripts/x_post_views.py apply \
  --view <投稿ID1>=<表示回数1> \
  --view <投稿ID2>=<表示回数2> \
  --measured-at <計測日時のISO 8601>
```

7. 次を順番に実行する

```bash
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/verify_theme_page.py
python3 scripts/build_admin_dashboard.py
```

8. 全て成功し、`x-posts.md` と管理画面の収集結果に値が出た場合だけコミットする

## 失敗時

- Chrome未接続・未ログイン・投稿が表示されない: ファイルを変更せず、理由を報告する
- 1件でも表示回数を特定できない: 一部だけ書かず、全件を次回へ送る
- 既存値の上書き拒否: 正常な保護動作として止め、手修正しない
- `<time>` は使わない。経過時間は投稿IDからスクリプトが算出する
- ログアウト状態、curl、公開APIで表示回数を取ろうとしない
