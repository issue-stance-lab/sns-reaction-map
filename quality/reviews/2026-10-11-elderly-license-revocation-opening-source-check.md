# 高齢者免許返納・冒頭試作の出典照合（2026-10-11）

対象: configs/elderly-license-revocation-opening.json / quality/designs/2026-10-11-elderly-license-revocation-opening.md の未確認事項
取得日 2026-10-11（WebFetch で一次資料を開き、本文と突き合わせた）

| 番号 | 冒頭の記述 | 出典URL | 取得できたか | 判定 | 根拠の引用（30字以内） | 直し案 |
|---|---|---|---|---|---|---|
| 1 | 全国一律の返納年齢は無い（自主返納は年齢を問わない） | https://www.npa.go.jp/policies/application/license_renewal/jishuhennou.html | 取得できた | 一致 | 「自主的に運転免許証を返納することができます」（年齢制限の記載なし） | - |
| 2 | 高齢者講習は70歳から（更新期間満了時の年齢） | https://laws.e-gov.go.jp/document?lawid=335AC0000000105 ／ https://www.npa.go.jp/policies/application/license_renewal/ninchi.html | 道路交通法は本文が取れず（下記）。警察庁ページは「臨時の高齢者講習」の記述のみ | 確認できず | - | - |
| 3 | 認知機能検査は75歳から | https://www.npa.go.jp/policies/application/license_renewal/ninchi.html | 取得できた | 一致 | 「75歳以上のドライバーは、認知機能検査等を受け」 | - |
| 4 | 運転経歴証明書は返納から5年以内に申請できる | https://www.npa.go.jp/policies/application/license_renewal/jishuhennou.html | 取得できた | 一致 | 「自主返納後５年以上…交付を受けることができません」（5年以内の裏返し。「申請期限」という語は本文に無い） | - |
| 5 | 2012年4月1日以降に交付された運転経歴証明書は本人確認書類になる | https://www.npa.go.jp/policies/application/license_renewal/jishuhennou.html | 取得できた | 一致 | 「平成24年４月１日以降に交付された運転経歴証明書は」 | - |
| 6 | 2025年の自主返納435,067件・運転経歴証明書の交付297,359件（マイナンバーカード記録分を含む注記あり） | https://www.npa.go.jp/publications/statistics/koutsuu/r07main.pdf | PDFを開いたが本文のテキストが圧縮されたまま読めず | 確認できず | - | - |
| 7 | 相談先「#8080」は警察の安全運転相談ダイヤル | https://www8.cao.go.jp/kourei/whitepaper/w-2025/html/zenbun/s2_2_4.html ／ 警察庁ページ | 取得できた | 確認できず | 白書は「全国統一の専用相談ダイヤル「#8080」」と書くが、警察が運営するとの記載は無い。警察庁ページにも#8080の記述は無い | - |
| 8 | タクシー割引などの特典は自治体・事業者ごとに違う | （今回の照合では確かめていない） | - | 確認できず | - | - |

## 補足

- 項目2: e-Gov 法令検索は本文が取れなかった（最初の URL は laws.e-gov.go.jp へ転送され、転送先でも条文は出なかった）。道路交通法の第百八条の二（高齢者講習）の条文は未確認。一次資料メモに書かれた条番号は、このページでは確かめていない。
- 項目5: 警察庁の案内そのものに記載があった。一次資料メモには無かった記述なので、メモの補記が必要。
- 項目7: 「警察の」という語は、いま開けた2ページのどちらにも無い。#8080が警察の窓口であることを示すには、別の警察庁ページを開いて確かめる必要がある（今回は代用していない）。
- 項目8: 今回の取得対象に入れていなかった。割引の記述は、警察庁ページか自治体ページで別途確かめる。

## 取得できなかったURL（本文が読めなかったもの）

- https://laws.e-gov.go.jp/document?lawid=335AC0000000105 （転送後も条文本文なし。https://elaws.e-gov.go.jp/ 経由でも同じ転送先）
- https://www.npa.go.jp/publications/statistics/koutsuu/r07main.pdf （PDF。本文テキストが圧縮されており読めず）

## PDFで本文が読めなかったもの

- 「運転免許統計 令和7年版」（r07main.pdf）: 自主返納435,067件、運転経歴証明書297,359件、マイナンバーカード記録分の注記のいずれも確認できず。

## 集計

- 一致: 4件（1, 3, 4, 5）
- 不一致: 0件
- 確認できず: 4件（2, 6, 7, 8）
