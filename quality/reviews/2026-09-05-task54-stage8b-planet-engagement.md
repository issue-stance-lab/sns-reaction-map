# 課題54 段階8-B：山なみへの作り替えと滞在の仕掛け（2026-09-05）

`tasks/task-54.md` の400行上限のため切り出した（2026-09-15）。当時の作業ログで、
記載されている作業ツリー・未マージコミット等の状態は段階3（2026-09-10）で
main へ統合済み。現在は無効な記述として参照しないこと。要約は `tasks/task-54.md`
の工程表・段階8-B行を見れば足りる。

---

オーナー指示「10分以上とどまらせる仕掛けを」から始まり、**球の廃止（案A）**まで進んだ一連の作業。
**経緯・やめた案・検査の中身は `quality/designs/planet-engagement-ideas.md` が正典。**

**やったこと**: ①球を廃止し、横から見た断面図（山なみ）にした。標高を球面の等高線で描いていたため
回しても正面から読めなかったのが理由 ②公開データ契約へ立場ごとの表現の強さを追加し、
幅と高さを同じ母数で数えられるようにした（受け皿・指導者の高さが立場により 15.9%→30.9% と動く）
③予想2問・潜水・一次資料クイズ7問・100マス・探査記録22地点を実装した。

**触っていないもの**: `docs/`（公開サイト）と `data/public/` の表示内容。差分0。

**実測**: 通しで操作して探査記録が 0→2→9→15→22/22。全470テストOK、検査5本OK、
2回生成の差分0、幅900pxで横スクロールなし。

**成果物の置き場所（当時の記録。作業ツリーは段階3で統合済み・削除済み）**:

- **作業ツリー**: `../isa-wt-planet-engagement`（ブランチ `task/planet-engagement`）
- 見る: `python3 scripts/build_planet_data.py --topic bukatsu-chiiki --prototype` を実行し、
  `quality/prototypes/bukatsu-chiiki-planet.html` を開く（データを埋め込んであるのでサーバー不要）
- 触ったファイル: `scripts/build_planet_data.py` / `scripts/public_registry_common.py` /
  `schemas/public-theme.schema.json` / `quality/prototypes/planet-prototype.template.html` /
  `tests/test_planet_data.py` / `tests/test_public_data_contract.py`

**当時残っていたこと（2026-09-06のオーナー承認を反映、以降の段階で解消済み）**:

1. **公開前に直す2点**: 表紙画像の先読み指定（`<link rel="preload">`）と
   広告枠の高さ確保（`min-height`）。共通部分を修正して効果を確認する
2. 設計書 `reaction-planet-renewal.md` 本文の書き直し（冒頭に無効の注記だけ入れてある）
3. 残り7テーマへの展開（段階10）
4. 段階11の総合監査と公開承認。段階9の共通仕様承認を公開承認とは扱わない

**確認済みの範囲**: オーナーのiPhoneでの見本確認と横展開承認は済んだ。
AIによるiPhone実機上の進み具合の再現確認はできていない（冒頭の修正記録参照）。
実広告が配信された状態での性能も未測定。「視差効果を減らす」設定は3テーマとも確認済み。
