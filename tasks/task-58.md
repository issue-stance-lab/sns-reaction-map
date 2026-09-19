# 課題58: 10テーマの一次資料メモをmainに反映済み。ページへの反映が未着手


**状態**: 調査・定期更新の仕組みとも 2026-09-01 にmainへマージ・push・作業ツリー片付け完了
**優先度**: 中（FACT_CHECK_GUIDE.mdの横展開対象4テーマ＋見直し対象6テーマの土台になる調査）

**やったこと**: hermes（別モデル、kimi-k2.6）に10テーマ（takaichi除く公開中の全テーマ）の一次資料調査を
並列発注し、その後オーナーから提示されたURL群を1件ずつ実際に開いて確認しながら、機械的な照合
（国会会議録APIでの発言原文照合、e-Gov法令検索APIでの条文照合、URL到達性のcurl検査）を重ねて
精度を上げた。成果物は `quality/research/{テーマ}-primary-sources.md`（テーマごと）と
`quality/research/README.md`（一覧・限界の記録）。

**質を上げるためにやったこと（今後の同種作業にも使える手順）**:
- 一次資料の定義（省庁・国会会議録・e-Gov・自治体・政党の公表資料）に厳密に従い、民間シンクタンク・
  事業者団体・まとめブログは不採用（一部、日本中体連のような「その団体自身の規則」はオーナー了承の上で例外採用）
- hermesが作った捏造URL（会議録名をそのままURLエンコードしただけの実在しないID）を1件検出・修正
- hermesが発言を「である調」に書き換えてから引用符で囲んでいた箇所を、機械照合で発見・原文へ訂正
- 一次資料の記述ミス（前回自分が書いた「都への名称変更条項」）を、成立法本体をe-Govで再確認して訂正

**定期更新の仕組み（2026-09-01 追加）**: 「オーナーと1件ずつ深掘りする」やり方は精度は高いが
定期運用には向かないため、他の定例作業と同じ「期日が来たら管理ダッシュボードが検知する」方式に乗せた。
- `quality/research/status.yaml`（`task/primary-research` 側）にテーマごとの最終確認日を記録
- `scripts/admin_dashboard/collect.py` の `collect_primary_research()` が
  90日（テーマによっては短縮）を過ぎた・一度も確認していないテーマを検知し、ダッシュボードに出す
- 手順は `.claude/skills/primary-research/SKILL.md` に固定化

**まだ終わっていないこと**:
1. **`quality/research/` はページに載せる前提のメモであり、そのままでは公開しない。** 各テーマの
   実際のページ（`docs/*.html`）に「投稿の主張を一次資料と突き合わせる」セクションとして反映する作業
   （FACT_CHECK_GUIDE.mdの手順）は別途必要
2. 一次資料メモ自体にも「確認できなかったこと」が各テーマに残っている（財源・費用系が特に弱い）

**テーマ別の厚み（2026-08-31時点、偏りがあるので着手順の参考に）**:
- **厚い**（オーナー提示のURLを多数確認済み）: ai-copyright（21本）、bike-blue-ticket、bukatsu-chiiki、
  constitutional-amendment、fukushuto、consumption-tax-cut、elderly-license-revocation
- **薄い**（初回のhermes生成のみ、または着手直後）: henoko-student-accident（着手済み、教育基本法14条
  違反の是正指導・追悼決議の不存在を確認したが「確認できなかったこと」がまだ4件残る）、
  **koshitsu-tenpakai（着手直後。改正法＝令和8年法律第66号の法律番号は確定したが、施行日が
  令和8年10月24日頃で、本メモ確認時点ではまだ全面施行されていない可能性が高いことが判明。
  実質的な改正内容〔婚姻後の皇籍維持等〕はe-Gov APIが附則を「抜粋」でしか返さず未確認のまま。
  「確認できなかったこと」6件中、法律番号の特定以外は未解消）**、school-nickname-ban（未着手）

## 課題64からの引き継ぎ（2026-09-07）

課題64（部活動テーマの一次資料メモの照合）が完了し、**ページへの反映だけがこの課題に残った。**

- **bukatsu-chiiki が全テーマで最も厚くなった。** 全9節・資料約30本がすべて本文照合済み
  （指導者／費用／送迎／教員負担／地域格差／生徒の選択肢／学習指導要領／制度の枠組み／事故の補償）。
  未解決リスト8項目もすべて解消。**パイロットの第一候補を ai-copyright から bukatsu-chiiki へ変える
  ことを勧める**（照合の精度が揃っており、「メモがどこまで使えるか」の検証に適しているため）。
- **ページに載せる価値が高いと判断した論点**: 第9節「事故が起きたときの補償」。
  学校の部活動はJSCの災害共済給付、地域クラブ活動は民間保険と、**移行で補償の枠組みが入れ替わる**。
  他のメディアがまだ扱っておらず、保護者の関心に直結する。
- **2026-09-07、オーナー判断でページ反映は保留。** 理由は課題54（Websiteリニューアル）の進行と
  当たるため。**課題54の段階10（残り7テーマ展開）と順番を調整してから着手すること。**

**次にすること**: 保留が解けたら、bukatsu-chiiki 1テーマでページ実装を試し、`quality/research/` の
情報がどの程度使えるか検証する（FACT_CHECK_GUIDE.mdの発注文に沿う）。
koshitsu-tenpakaiは施行日（令和8年10月24日頃）以降にe-Govをブラウザで直接開くか
官報で附則全文を確認するのが本筋で、これは上とは独立に進められる。

## bukatsu-chikiiでのパイロット実施（2026-09-20）

オーナー指示（消費税減税の「その言い分、原典に当たるとどうなるか」をbukatsu-chiikiにも作れるか）を
きっかけに、保留を解いて着手した。ただし対象は`quality/research/bukatsu-chiiki-primary-sources.md`
（全9節・約30本）そのものではなく、そこから既に切り出されて`scripts/build_bukatsu_process_sections.py`の
`FACT_CHECKS`（7件、2026-09-02時点で確定）として構造化済みだった一次資料照合カードのほう。
このデータは`public_registry_common.py`のCLAIM_AUDIT_SOURCESに既に登録されており、公開JSONの
`claim_verification`も既に生成されていたが、**ページ側（docs/bukatsu-chiiki-reaction-map.html）には
一度も表示されていなかった**（他8テーマの同種スクリプトも同じ状態。表示済みなのは
consumption-tax-cut・koshitsu-tenpakaiの2テーマだけと判明）。

koshitsu-tenpakaiが2026-09-20（同日）に「消費税と同じ見た目に揃える」形でオーナー指摘を受けて
作り直したばかりだったため、そのbuild_koshitsu_process_sections.pyを最新の型として複製した。
PLANET_SECTIONの外（`<!-- BUKATSU_AUDIT_START/END -->`、定期更新では書き換わらない区間）へ
「その言い分、原典に当たるとどうなるか」節を新設し、`build_bukatsu_process_sections.py`の`main()`が
`write_provenance_records()`と併せてHTMLへ差し込むよう変更した。判定マーク（原典どおり/原典とズレ/
原典に届かず）は消費税・皇室典範と共通の固定3語にし、bukatsu-chiiki独自だった`verdict_label`
（2026-09-02時点の「他テーマと表現を重ねない」方針の名残）はこの節では使っていない。

**素の複製では通らなかった点**: lead/how文をconsumption-tax-cutの文面からほぼそのまま流用したところ、
`verify_page_originality.py`が4文の使い回しを検出（NG）。koshitsu-tenpakaiは独自に言い換えていたため
気づかず、bukatsu独自の言い回しに書き直して解消した。件数（`ca-n`・`ca-how`）の出所は
`configs/bukatsu-chiiki-reaction-map.json`の`number_provenance.sources`にconsumption-tax-cutと
同じ形で登録が必要だった（未登録だと`verify_number_provenance.py`がNG）。

標準検査4種・unittest 984件・run_public_checks.py・verify_claim_verdicts.pyいずれもNG0件。
ブラウザでデスクトップ・375pxモバイル幅とも表示を確認済み。

**まだ終わっていないこと（変わらず）**: 一次資料メモ本体（全9節）のうち、ページに反映したのは
FACT_CHECKSの7件（事実確認カード）だけ。指導者・送迎・学習指導要領など、それ以外の記述を
ページへどう載せるか（第9節「事故が起きたときの補償」を含む）は未着手のまま。
なお「これまでの経緯」（背景タイムライン）は`build_background()`経由で別途既に反映済みで、
これも一次資料メモが原資料になっている。

作業は`../isa-wt-bukatsu-claim-audit`（ブランチ`task/bukatsu-claim-audit`）で行った。
