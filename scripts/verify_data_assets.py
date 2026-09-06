#!/usr/bin/env python3
"""Git管理ファイルだけで、保存境界と復元記録の整合を検査する。"""
import json
import re
from pathlib import Path
import yaml
try:
    from .data_asset_inventory import ROOT,OUT,PRIVATE_RECEIPT,EXTERNAL_RECEIPT,read,sha,git_paths,safe_path,coverage,external_requirements
except ImportError:
    from data_asset_inventory import ROOT,OUT,PRIVATE_RECEIPT,EXTERNAL_RECEIPT,read,sha,git_paths,safe_path,coverage,external_requirements
from collections import Counter
from datetime import datetime


def require(value,message):
    if not value:raise ValueError(message)

def validate_receipt(receipt):
    required={'schema_version','verified_at','git_commit','archive_name','archive_sha256','file_count','total_bytes','files','restore_verified'}
    require(required<=set(receipt)<=required|{'git_tracked_dirty'},'復元記録の形式不一致')
    require(receipt['schema_version']==1 and receipt['restore_verified'] is True,'復元が未確認')
    require(datetime.fromisoformat(receipt['verified_at']).tzinfo is not None,'復元日時のタイムゾーン欠落')
    require(re.fullmatch('[0-9a-f]{40}',receipt['git_commit']) is not None,'Git版が不正')
    safe_path(receipt['archive_name']);require('/' not in receipt['archive_name'],'アーカイブ名に保存先を含めない')
    require(re.fullmatch('[0-9a-f]{64}',receipt['archive_sha256']) is not None,'アーカイブ指紋が不正')
    names=set()
    for row in receipt['files']:
        require(set(row)=={'path','bytes','sha256','records'},'復元ファイルに余分な項目')
        safe_path(row['path']);require(row['path'] not in names,'復元ファイル重複');names.add(row['path'])
        require(type(row['bytes']) is int and row['bytes']>=0,'ファイルサイズ不正')
        require(re.fullmatch('[0-9a-f]{64}',row['sha256']) is not None,'ファイル指紋不正')
        require(row['records'] is None or type(row['records']) is int and row['records']>=0,'件数不正')
    require(receipt['file_count']==len(names),'復元ファイル件数不一致')
    require(receipt['total_bytes']==sum(r['bytes'] for r in receipt['files']),'復元サイズ集計不一致')


def verify(root=ROOT):
    root=Path(root);data=read(root/OUT);tracked=git_paths(root)
    require(set(data)=={'schema_version','snapshot_at','git_commit','scope','files','summary','canonical','backup'},'資産形式不一致')
    require(data['schema_version']==1,'資産版不一致')
    require(data['scope']=='all_social_samples_plus_persona_and_active_adoption_evidence','資産範囲不一致')
    require(datetime.fromisoformat(data['snapshot_at']).tzinfo is not None,'資産日時不正')
    require(re.fullmatch('[0-9a-f]{40}',data['git_commit']) is not None,'資産Git版不正')
    names=set();by_path={}
    for row in data['files']:
        require(set(row)=={'path','storage','sha256','bytes','roles'},'資産に余分な項目')
        safe_path(row['path']);pair=(row['storage'],row['path'])
        require(pair not in names,'資産重複');names.add(pair)
        require(row['storage'] in {'git','private_backup','external_evidence'},'不明な保存先')
        require(type(row['bytes']) is int and row['bytes']>=0,'資産サイズ不正')
        require(re.fullmatch('[0-9a-f]{64}',row['sha256']) is not None,'資産指紋不正')
        require(isinstance(row['roles'],list) and row['roles'] and set(row['roles'])<=
                {'canonical','saved_update','legacy_or_support','private_persona','adoption_evidence'},'資産役割不正')
        if row['storage']=='git':
            require(row['path'] in tracked and sha(root/row['path'])==row['sha256'],'Git資産が変わっています: '+row['path'])
        elif row['storage']=='private_backup':require(row['path'] not in tracked,'非公開資産がGitへ移動')
        if row['storage']!='external_evidence':by_path[row['path']]=row
    require({p for p in tracked if p.startswith('social-samples/')}=={r['path'] for r in data['files'] if r['storage']=='git'},'Git資産一覧の欠落・追加')
    require(data['summary']==dict(Counter(r['storage'] for r in data['files'])),'資産集計不一致')
    themes=yaml.safe_load((root/'THEMES.yaml').read_text())['themes']
    require(data['canonical']=={t:{'path':d['sample_file'],'storage':by_path[d['sample_file']]['storage']} for t,d in themes.items()},'正典保存境界不一致')
    require({r['path']:r['sha256'] for r in data['files'] if r['storage']=='external_evidence'}==external_requirements(root),'採否根拠の参照が変わっています')
    for label,storage,file in [('private','private_backup',PRIVATE_RECEIPT),('external','external_evidence',EXTERNAL_RECEIPT)]:
        validate_receipt(read(root/file))
        actual=coverage([r for r in data['files'] if r['storage']==storage],root/file)
        require(actual==data['backup'][label] and actual['status']=='verified','保全対象が未保存または内容不一致')
    return data['summary']

if __name__=='__main__':
    try:print('OK 保存境界と復元記録',verify())
    except (ValueError,KeyError,TypeError,OSError) as e:raise SystemExit('NG データ保全: '+str(e))
