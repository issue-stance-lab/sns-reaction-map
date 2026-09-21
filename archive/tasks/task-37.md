# 課題37: validate_theme_seo.py が1件落ちている

**状態**: 完了（2026-09-21）
**発見**: 2026-08-07

```
FAILED: 1 validation error(s)
- ai-copyright-reaction-map.html: dateModified does not match THEMES.yaml updated_at
```

**概要**: `docs/ai-copyright-reaction-map.html` の JSON-LD `dateModified` と `THEMES.yaml` の `updated_at` がずれている。データ更新時にページ側のSEO日付を戻し忘れたと思われる。

## 2026-09-21: 再確認・完了

**症状は解消済み**。`validate_theme_seo.py` を実行してもエラーは出ず、両方の値を直接見比べても
`THEMES.yaml` の `updated_at`・HTML内の `dateModified` とも `2026-09-20` で一致している。

**いつ・何の作業で直ったかは特定できていない**（6週間分のコミットを1つずつ追う調査はしていない）。
そのため、代わりに「今の仕組みに、同じズレを再び生む欠陥が残っていないか」を確認した。

**確認した4つの更新経路（すべてTHEMES.yamlの`updated_at`とページ内`dateModified`を同時に書く設計）**:
1. `scripts/refresh_topic.py` の `promote()`（10テーマ共通の本昇格）— `updated_at` 書き込み直後に
   `update_seo_date()` を呼び、`configs/theme-seo.json` の `dateModified` も同じ `current_date` で更新
2. 同ファイルの候補生成関数（公開前プレビュー版）— 同様に対で更新
3. `scripts/refresh_bukatsu_pilot.py`（部活動テーマ専用）— 同じ対応関係
4. `scripts/build_consumption_tax_page.py`（消費税減税テーマ専用）— こちらは逆に「日付は
   `apply_theme_trust.py`が`configs/theme-seo.json`から管理する値なので、このスクリプトが
   初版の日付で塗り直すと更新日が巻き戻る」という注意書きつきで、意図的に日付を触らない設計

4経路とも、片方だけ更新されてもう片方が取り残される抜け道は見つからなかった。

**もう1つの手がかり**: この検査（`validate_theme_seo.py`）が `run_public_checks.py` 経由で
push のたびに自動実行されるようになったのは **2026-09-02**（コミット`80814bdb`）で、
2026-08-07の発見時点ではまだ手動実行のみだった。つまり当時は「気づいた人が手動で走らせない限り
ズレに気づけない」状態だったが、9/2以降は同じズレが今後起きれば自動検査で止まる。

**結論**: 元の原因（おそらく手動編集か、当時の別経路によるページ再生成）の特定はできなかったが、
現在の4つの更新経路すべてに同種の欠陥が無いこと、および9/2以降は自動検査が常設されていることを
確認できたため、これ以上の追跡はせず完了とする。
