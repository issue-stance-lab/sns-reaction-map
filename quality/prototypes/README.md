# 「議論の惑星」試作

非公開の試作です。公開サイト（`docs/`）には入っていません。

## 見る

`bukatsu-chiiki-planet.html` をダブルクリックするだけです。
データを中に埋め込んであるので、サーバーもネット接続も要りません。

## データが増えたときの作り直し

```
python3 scripts/build_planet_data.py --topic bukatsu-chiiki
```

これだけで、件数・大陸の面積・色・山の高さ・島の分かれ方が全部作り直されます。
HTMLには数字が1つも書かれていないので、手で直すところはありません。

## 何をどこで決めているか

| やりたいこと | 触るファイル |
|---|---|
| 立場の色・並び、論点のアイコン、島の元データの場所 | `configs/planet/bukatsu-chiiki.yaml` |
| 面積・色・高さの計算、大陸の位置 | `scripts/build_planet_data.py` |
| 見た目・操作・アニメーション | `quality/prototypes/planet-prototype.template.html` |
| 出来上がったデータ（確認用） | `quality/prototypes/data/bukatsu-chiiki-planet.json` |

論点が増えたときは `configs/planet/bukatsu-chiiki.yaml` の `issues:` に1行足すだけです。
**既存の `id` は変えないこと**（URLと投票の互換が壊れます）。

新しいテーマへ広げるときは、`configs/planet/{テーマID}.yaml` を作って
同じコマンドを `--topic {テーマID}` で実行します。HTMLもスクリプトも共通のままです。

## 3Dが描けない環境での表示

JavaScriptが無効な端末や、canvas が使えない環境では、同じ内容を静的な一覧で表示します。
このHTMLも `build_planet_data.py` が data から作ります（**手で書かないこと**）。
手書きの数字を入れると `tests/test_planet_data.py` の `PlanetPageTest` が落ちます。

## この試作で確認していないこと

- 実機のスマホでの操作感（ブラウザの開発ツール上の375px幅でのみ確認）
- 「視差効果を減らす」設定をONにしたときの動き
- 代表投稿の表示（現行993意見での存在確認が済んでいないため、まだ載せていない）
- 沈んだ大陸・地下水脈（生成器は出しているが、画面にはまだ出していない）
