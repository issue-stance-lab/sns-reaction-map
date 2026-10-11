# 憲法改正の冒頭試作 出典突き合わせ（2026-10-11）

対象: `configs/constitutional-amendment-opening.json` の主張と出典URL
設計書: `quality/designs/2026-10-11-constitutional-amendment-opening.md`（未確認事項）
取得日 2026-10-11（WebFetch）

判定の基準: 一致＝出典本文で確認できた。不一致＝出典本文と違う。確認できず＝本文を取得できなかった、または読めなかった（別の資料で代用していない）。

## 結果

- 一致 2件（No.7 2026年7月成立、No.11 第221回国会の討議）
- 不一致 0件
- 確認できず 11件

## 突き合わせ表

| 番号 | 冒頭の記述 | 出典URL | 取得できたか | 判定 | 根拠の引用（30字以内） | 直し案 |
|---|---|---|---|---|---|---|
| 1 | 憲法96条: 衆参それぞれ総議員の3分の2以上で発議 | https://laws.e-gov.go.jp/law/321CONSTITUTION | 開いたが本文なし（ページ見出しのみ） | 確認できず | — | — |
| 2 | 憲法96条: 国民投票で過半数の賛成で承認 | https://laws.e-gov.go.jp/law/321CONSTITUTION | 同上 | 確認できず | — | — |
| 3 | 発議から60日以後180日以内に投票 | https://laws.e-gov.go.jp/law/419AC1000000051 | 開いたが本文なし | 確認できず | — | — |
| 4 | 「過半数」は賛成票が賛否合計の半分を超えること | https://laws.e-gov.go.jp/law/419AC1000000051 | 同上 | 確認できず | — | — |
| 5 | 最低投票率の定めなし | https://laws.e-gov.go.jp/law/419AC1000000051 | 同上 | 確認できず | — | — |
| 6 | 2026年7月成立の改正の施行が10月31日 | https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/keika/1DE28DE.htm | 一部（文字化けあり） | 確認できず | 施行日の記載なし。公布は令和8年7月31日（法律第73号）と読めた | 施行日は別途確認が必要。出典ページには無いので、出典の差し替えも検討 |
| 7 | 2026年7月に成立（投票の実務を整える改正） | 同上 | 一部（文字化けあり） | 一致 | 参議院の議決日として令和8年7月24日と読めた。「実務を整える」内容の記述は確認していない | 文字化けを目視で再確認 |
| 8 | FAQ「日本国憲法は改正0回」 | https://laws.e-gov.go.jp/law/321CONSTITUTION（および自民党資料） | 本文なし／自民党資料は読めず | 確認できず | — | — |
| 9 | 2018年、自民党が9条1・2項を残して自衛隊を明記する案 | https://storage.jimin.jp/pdf/constitution/document/kenpou_manual2026.pdf | 302で別ドメインへ転送後、PDFの生データのみ（本文は読めず） | 確認できず | — | — |
| 10 | 2026年5月、緊急事態条項の議員用イメージ案が衆議院で示された | https://www.shugiin.go.jp/Internet/itdb_kenpou.nsf/html/kenpou/2210514housei_kenshin-siryou.pdf/$File/2210514housei_kenshin-siryou.pdf | PDFの生データのみ（本文は読めず） | 確認できず | — | — |
| 11 | 直近の通常国会（第221回）で緊急事態条項や9条を討議 | https://www.shugiin.go.jp/Internet/itdb_kenpou.nsf/html/kenpou/221.htm | 取得（要約者が読んだ見出し。文字化けあり） | 一致 | 第5号 令和8年5月14日「『緊急事態条項』のイメージ（再）」、第10号 令和8年6月18日「9条に関する集中的な討議」 | 見出しを目視で再確認 |
| 12 | 9条に「自衛隊」の語はない／現行憲法に緊急事態条項の名称の規定はない | https://laws.e-gov.go.jp/law/321CONSTITUTION | 本文なし | 確認できず | — | — |
| 13 | 発議には衆議院100人以上・参議院50人以上の賛成で原案提出、個別発議 | https://www.shugiin.go.jp/internet/itdb_kenpou.nsf/html/kenpou/r8_shiryosyu.pdf/$File/r8_shiryosyu.pdf | PDFの生データのみ（本文は読めず） | 確認できず | — | — |

注: No.10 について、第221回の討議記録（No.11の出典）には「『緊急事態条項』のイメージ」の見出しが読めた。ただし、これは別の出典であり、イメージ案PDFの内容確認にはならないので、No.10 は確認できずのままにした。

## 開けなかったURL・本文が取れなかったURL

- https://laws.e-gov.go.jp/law/321CONSTITUTION: ページは開いたが本文が取れなかった（見出しのみ）
- https://laws.e-gov.go.jp/law/419AC1000000051: 同上
- https://laws.e-gov.go.jp/api/2/lawdata/321CONSTITUTION: 404（代わりのURLとして試したが、出典にはしていない）
- https://laws.e-gov.go.jp/api/2/lawdata/419AC1000000051: 404（同上）
- https://storage.jimin.jp/pdf/constitution/document/kenpou_manual2026.pdf: 302で https://storage2.jimin.jp/... へ転送。転送先もPDFの生データのみ
- https://www.shugiin.go.jp/Internet/itdb_kenpou.nsf/html/kenpou/2210514housei_kenshin-siryou.pdf/$File/2210514housei_kenshin-siryou.pdf: 開けたがPDFの生データのみ

## PDFで本文が読めなかったもの

- 衆議院憲法審査会 関係資料集 令和8年版（r8_shiryosyu.pdf）: 本文なし（No.13）
- 自民党 憲法改正の解説 2026年版（kenpou_manual2026.pdf）: 本文なし（No.8・No.9）
- 衆議院 緊急事態条項のイメージ案（2026年5月14日）: 本文なし（No.10）

## 次の確認（オーナーまたは別の作業者）

- e-Gov の本文（No.1〜5・8・12）は、ブラウザで開いて目視確認するのが確実。
- 上記PDFは、ローカルで `pdftotext -layout` などで文字を取り出して照合する。
- 施行日10月31日（No.6）は、出典ページに無いので、出典の差し替えが必要かもしれない。
