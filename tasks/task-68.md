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

**次にすること**: `data/verification/adoption/registry.json` のai-copyright関連エントリを、
2026-09-14のai-copyright変更（`a6b8340`）の内容を確認した上で、正しい指紋に更新する。
`python3 scripts/verify_adoption_registry.py` がOKになることを確認する。

**判断待ち**: 上記の指紋更新が妥当か（課題63担当、またはai-copyright山なみ移行の経緯を
把握しているセッション）。

## 影響

CIの「公開ファイルの検査」は2026-09-13 13:17以降、この1件により失敗し続けている
（Deploy自体は別ジョブで成功しており、公開サイトへの反映は妨げられていない）。
赤が常態化すると、次に本当に重大な壊れ方が起きても気づきにくくなる。
