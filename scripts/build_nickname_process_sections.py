"""あだ名禁止の一次資料照合。公開契約から新ページへ接続する。

担当: Codex AI。現行110意見の独立確認は quality/reviews/2026-10-31-nickname-four-claims-resolution.json。
判例調査の未完了範囲は quality/reviews/2026-10-31-nickname-case-search-retry.json。
別担当による公開前監査とは区別する。
"""
CHECKED_AT = "2026年10月31日"
FACT_CHECKS = [{'key': 'national-rule',
  'claim': '今の学校では、あだ名禁止が普通になっている',
  'verdict': 'miss',
  'issues': ['学校運用・現場体験'],
  'note': '確認した法律・国の基本方針・生徒指導提要には、あだ名禁止や全員さん付けを全国一律に求める記述は見当たりません。これだけでは導入校の割合も分かりません。個別の学校で導入されているという体験談と、全国的な普及の度合いを分けて読む必要があります。',
  'links': [('https://laws.e-gov.go.jp/law/425AC1000000071', 'e-Gov：いじめ防止対策推進法'),
            ('https://www.mext.go.jp/content/20230220-mxt_jidou01-000024699-201-1.pdf',
             '文部科学省：生徒指導提要（改訂版）')]},
 {'key': 'constitution',
  'claim': 'あだ名禁止は憲法違反なので従う必要がない',
  'verdict': 'miss',
  'issues': ['一律禁止の実効性'],
  'note': 'この断言を支える判例は特定できませんでした。10月31日の再試行も裁判所の検索機能が保守中で、判例調査は一部未完了です。生徒指導提要は校則に教育目的と社会通念上の合理性を求めています。検索不能を、判例の不存在や一律の合憲・違憲の根拠にはできません。',
  'links': [('https://www.mext.go.jp/content/20230220-mxt_jidou01-000024699-201-1.pdf',
             '文部科学省：生徒指導提要（改訂版）')]},
 {'key': 'rule-reason',
  'claim': 'ルールは、禁止の理由を理解できるように指導する必要がある',
  'verdict': 'fact',
  'issues': ['一律禁止の実効性', 'さん付け・ジェンダー配慮'],
  'note': '生徒指導提要の「校則の運用」は、守らせることだけにこだわらず、背景や理由を教職員が理解し、児童生徒自身が意味を理解するよう指導することを求めています。特定の呼称ルールへの賛否を国が指定したものではありません。',
  'links': [('https://www.mext.go.jp/content/20230220-mxt_jidou01-000024699-201-1.pdf',
             '文部科学省：生徒指導提要（改訂版）')]},
 {'key': 'unwanted-name',
  'claim': '嫌な呼び名が、いじめにつながることがある',
  'verdict': 'fact',
  'issues': ['いじめ・心理的安全', '本人意思・柔軟運用'],
  'note': '法律は、一定の人的関係にある他の児童生徒から心理的・物理的な影響を受け、対象となった子供が心身の苦痛を感じる行為をいじめと定義しています。基本方針も、被害性に着目する考え方です。あだ名という形式だけで一律に決まるわけではなく、個別の事情の確認が要ります。',
  'links': [('https://laws.e-gov.go.jp/law/425AC1000000071', 'e-Gov：いじめ防止対策推進法'),
            ('https://www.mext.go.jp/component/a_menu/education/detail/__icsFiles/afieldfile/2019/06/26/1400030_007.pdf',
             '文部科学省：いじめの防止等のための基本的な方針'),
            ('https://www.mext.go.jp/a_menu/shotou/seitoshidou/__icsFiles/afieldfile/2018/09/25/1409466_001_1.pdf#page=14',
             '文部科学省：いじめ対応の事例集・Case03（本文12〜13頁）')]}]
