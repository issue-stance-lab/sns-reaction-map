# 課題68: ai-copyrightの採用台帳がpushのたびにCIを赤くしている

**発見の経緯**: 2026-09-15、課題54（皇室典範）の本番反映作業で、GitHub Actionsの
「公開ファイルの検査」（`.github/workflows/checks.yml` → `scripts/run_public_checks.py`）が
複数回連続で失敗しているのに気づいた。皇室典範側の原因（非公開データへの依存3件）は
特定・修正し解消したが、`scripts/verify_adoption_registry.py` の1件だけ残った。

## 症状

```
NG 採用台帳: snapshot fingerprint changed: data/public/themes/ai-copyright.json
```

`data/verification/adoption/registry.json`（採用台帳）に記録された
`data/public/themes/ai-copyright.json` のsha256指紋が、現在のファイルの指紋と一致しない。

## 原因（推定）

`git log -- data/public/themes/ai-copyright.json` を見ると、最後の変更は
`a6b8340`「feat(ai-copyright): 山なみ形式へローカル差し替え（本番反映はまだ）」
（2026-09-14 18:27、一次資料突き合わせ・編集部の横断整理を新規作成してindependence_gateを通した
という内容）。このコミットは同日中にmainへマージ・pushされていた（課題54作業の着手前から
既にorigin/mainに存在。課題54とは無関係）。

一方、採用台帳 `data/verification/adoption/registry.json` の最終更新は
`adf90f8`（2026-09-13 20:37、fukushuto関連）で、ai-copyrightの2026-09-14の変更を
反映できていない。**採用台帳の指紋更新が、ai-copyrightの山なみ差し替え作業の
どこかの手順から漏れたと見られる。**

## 対応方針の判断が必要な理由

採用台帳は課題63（Xデータの定期収集を資産として整える）が管理する監査証跡（decision_seed等、
意見の採用・保留判断の記録）で、課題54からは中身の妥当性を判断できない。単純に現在の
ai-copyright.jsonの指紋で上書きするだけなら技術的には可能だが、それが「正しい状態への
追いつき」なのか「未承認の変更を追認してしまう」のか、課題63・ai-copyright山なみ移行の
文脈を持つ担当でないと判断できない。

**判断待ち**: 上記の指紋更新が妥当か（課題63担当、またはai-copyright山なみ移行の経緯を
把握しているセッション）。

## 影響

CIの「公開ファイルの検査」は2026-09-13 13:17以降、この1件により失敗し続けている
（Deploy自体は別ジョブで成功しており、公開サイトへの反映は妨げられていない）。
赤が常態化すると、次に本当に重大な壊れ方が起きても気づきにくくなる。

## 対応・完了（2026-09-15）

課題54の段階11（総合監査）の一環で `python3 scripts/verify_adoption_registry.py` を実行したところ、
ai-copyrightに加えて **consumption-tax-cut・koshitsu-tenpakaiの2テーマも同種の指紋不一致**を検出した
（`verify_adoption_registry.py` は`require()`で最初のNGだけ報告して打ち切る実装のため、ai-copyright以外は
これまで報告されていなかった）。`build_adoption_registry.py --check` で差分を確認し、3テーマとも
`public_sha256` のみが変化（koshitsu-tenpakaiのみ`canonical_file`もTHEMES.yamlの現行`sample_file`
（`social-samples/koshitsu-tenpakai_release_20260913.json`、9/13候補統合分）と一致する形で変化）。
`records` 件数はai-copyright 3812・consumption-tax-cut 3762・koshitsu-tenpakai 1605のいずれも変化なしで、
`decision_seed`・`scope_config`・`cohorts`も無変化と確認した。3テーマとも課題54の正規の山なみ移行手順
（一次資料照合・編集部の横断整理→independence_gate通過→標準検査→本番反映）を経た承認済みの変更であり、
`build_adoption_registry.py`（「追加・削除・再分類は行わない」照合専用ツール）が機械的に指紋を再集計した
だけと判断できたため、`task/task68-adoption-registry` で再生成・検証して本番反映した。

**確認済み**: `verify_adoption_registry.py` OK（11トピック / 17,104レコード / 121ファイル）、
`test_adoption_registry.py` 12件OK、変化したトピックはai-copyright・consumption-tax-cut・
koshitsu-tenpakaiの3件のみ（他8テーマ・decision_seed等は無変化）。

**教訓**: 採用台帳（`data/verification/adoption/registry.json`）の再生成は、テーマの公開データ（`data/public/themes/*.json`）
を更新する山なみ移行作業の標準手順に含まれていない。今回のように複数テーマで同時に漏れる。
`release` スキルの本番反映チェックリストに `build_adoption_registry.py --check` を追加するか検討の余地がある
（課題63・課題54のどちらが担当するかは別途判断）。
