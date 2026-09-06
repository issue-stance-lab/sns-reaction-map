#!/usr/bin/env python3
"""固定した未再読262件の個別判断を検証し、本文なしの接続台帳を作る。"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE_REF = '9e328e38d8978eda4f61f95e60139258dfd1230f'
CANONICAL = 'social-samples/bike-blue-ticket_2d_classified.json'
PACKETS = ('other_a', 'other_b', 'support', 'remaining')
# 同じ意味の区分だけ統合し、個別判断と元の区分は外付け記録に保持する。
MERGES = {
 'oa_news_information': ('n_information','記事・制度案内・活動報告の共有'),
 'ob_news_share': ('n_information','記事・制度案内・活動報告の共有'),
 'ob_event_report': ('n_information','記事・制度案内・活動報告の共有'),
 'ob_system_information': ('n_information','記事・制度案内・活動報告の共有'),
 'ob_enforcement_report': ('n_information','記事・制度案内・活動報告の共有'),
 'ob_content_introduction': ('n_introduction','記事・動画・商品の紹介'),
 'oa_product_promotion': ('n_introduction','記事・動画・商品の紹介'),
 'oa_safety_awareness': ('n_education','交通ルールの理解と安全運転の呼びかけ'),
 'ob_rule_education': ('n_education','交通ルールの理解と安全運転の呼びかけ'),
 'oa_scam_prevention': ('n_fraud','反則金を口実にした詐欺への注意'),
 'ob_fraud_prevention': ('n_fraud','反則金を口実にした詐欺への注意'),
 'oa_context_unresolved': ('n_context','本人の立場や参照先の文脈が不足する反応'),
 'ob_unclear_stance': ('n_context','本人の立場や参照先の文脈が不足する反応'),
 'oa_mobility_burden': ('n_burden','利用時の負担・不安と行動への影響'),
 'ob_cost_and_use': ('n_burden','利用時の負担・不安と行動への影響'),
 'oa_alternative_transport': ('n_transport','自転車と別の移動手段の選択'),
 'ob_transport_change': ('n_transport','自転車と別の移動手段の選択'),
 'oa_rules_consistency': ('n_rules','交通ルールの解釈・例外・運用の整合性'),
 'ob_rule_interpretation': ('n_rules','交通ルールの解釈・例外・運用の整合性'),
 'oa_persistent_violations': ('n_effects','導入後の違反や行動の変化への見方'),
 'ob_enforcement_effectiveness': ('n_effects','導入後の違反や行動の変化への見方'),
 'ob_perceived_effect': ('n_effects','導入後の違反や行動の変化への見方'),
 'oa_infrastructure': ('n_environment','道路環境と制度の適合への意見'),
 'ob_local_conditions': ('n_environment','道路環境と制度の適合への意見'),
 'ob_urban_change': ('n_environment','道路環境と制度の適合への意見'),
 'oa_other_topic': ('n_other','青切符への言及を含む別の主題'),
 'ob_outside_topic': ('n_other','青切符への言及を含む別の主題'),
}


def sha(raw):
 return hashlib.sha256(raw).hexdigest()


def build(review_dir):
 manifest=json.loads((review_dir/'target-manifest.json').read_text())
 raw=(ROOT/CANONICAL).read_bytes()
 if sha(raw)!=manifest['canonical_sha256']:
  raise ValueError('固定した正典版と現在の原本が異なります')
 canonical={r['tweet_id']:r for r in json.loads(raw)}
 old=json.loads(subprocess.check_output(['git','show',f'{BASE_REF}:data/bike-blue-ticket_issues-reread.json'],cwd=ROOT))
 old_ids={r['tweet_id'] for v in old.values() if isinstance(v,dict) for r in v.get('items',[])}
 target=set(canonical)-old_ids
 definitions={};items=[];source_hashes={};dates=[];evidence=[]
 for name in PACKETS:
  source=review_dir/f'{name}-reviewed.json';review=json.loads(source.read_text())
  packet_path=review_dir/f'{name}-input.json';packet=json.loads(packet_path.read_text())
  if sha(packet_path.read_bytes())!=manifest['packets'][name]['sha256']:
   raise ValueError('固定入力の指紋が違います')
  ids=[r['tweet_id'] for r in review['items']]
  if len(ids)!=len(set(ids)) or set(ids)!={p['tweet_id'] for p in packet}:
   raise ValueError('担当対象の未読・重複・対象外IDがあります')
  source_hashes[source.name]=sha(source.read_bytes());dates.append(review['read_at'])
  for r in review['items']:
   p=canonical[r['tweet_id']]
   if r.get('text_sha256')!=sha(p['text'].encode()) or r['main_issue']!=p['classification']['main_issue']:
    raise ValueError('本文版または主論点が変化しています')
   if r.get('body_reviewed') is not True or r.get('review_kind')!='editorial_body_reread' or not r.get('reason'):
    raise ValueError('本文再読の根拠がありません')
   concern=r['classification_concern']
   if concern not in ('none','not_opinion_candidate','context_missing','possibly_off_topic'):
    raise ValueError('不明な懸念区分です')
   key,label=MERGES.get(r['bucket'],(r['bucket'],review['bucket_definitions'][r['bucket']]))
   if key in definitions and definitions[key]!=label:raise ValueError('区分名が衝突しています')
   definitions[key]=label
   item={k:r[k] for k in ('tweet_id','text_sha256','main_issue','review_kind','body_reviewed','classification_concern')}
   item.update(bucket=key,read_at=review['read_at'],reviewer=review['reviewer'],reason_sha256=sha(r['reason'].encode()),source_file=source.name)
   items.append(item);evidence.append(dict(r,final_bucket=key,read_at=review['read_at'],reviewer=review['reviewer']))
 all_ids=[r['tweet_id'] for r in items]
 if len(all_ids)!=len(set(all_ids)) or set(all_ids)!=target or len(target)!=262:
  raise ValueError('固定未再読262件を完全に覆っていません')
 out={'schema':1,'theme':'bike-blue-ticket','review_kind':'editorial_body_reread','reviewer_type':'editorial_ai',
      'read_at':max(dates),'target_base_commit':BASE_REF,'canonical_sha256':sha(raw),
      'target_sha256':sha('\n'.join(sorted(target)).encode()),'target_count':len(target),
      'method':'原文を個別再読し、別担当が全件を原文と再照合。分類器の要約を使わず、新しい分類候補は原本へ適用しない。',
      'evidence_note':'個別理由・懸念の説明・監査修正履歴は非公開保存。reason_sha256で結び付ける。',
      'source_sha256':source_hashes,'classification_concerns':dict(collections.Counter(r['classification_concern'] for r in items)),
      'bucket_definitions':dict(sorted(definitions.items())),'items':sorted(items,key=lambda r:r['tweet_id'])}
 return out,evidence


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--review-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--private-evidence',type=Path,required=True);a=ap.parse_args()
 out,evidence=build(a.review_dir)
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 a.private_evidence.parent.mkdir(parents=True,exist_ok=True);a.private_evidence.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'read':len(out['items']),'concerns':out['classification_concerns']},ensure_ascii=False))

if __name__=='__main__':main()
