"""Private candidate issue illustrations and publicly linked representative X posts."""
import html
from build_planet_page_preview import ISSUE_CSS

MEDIA = {
'patrilineal-matrilineal': ('keisho-v5', '男系を維持する考えと女系も認める考え、改正後も変わらない第一条を示す図解。', [('benjymin84/2081234225664262600','男系の継承を重視','女性天皇への否定とは分けて、男系の継承を続けたいと述べています。'),('a_aok04352/2080825663821615144','男女を問わない安定継承を求める','従来の仕組みを続ける難しさを挙げ、男女を問わず継承できる制度を求めています。')]),
'female-emperor': ('josei-tenno-v3', '女性天皇と女系天皇の違い、現行の継承資格を示す図解。', [('5VcfqTGE08SrXGE/2081146247327760862','女系への移行を懸念','結婚できる女性天皇が女系の継承につながることを懸念しています。'),('ayumuchan3/2081231595923734681','女性天皇となる可能性に言及','投稿者は、愛子さまの教育方針を、将来のさまざまな立場に備えるものと捉えています。')]),
'former-royal-adoption': ('yoshi-v3', '旧宮家につながる男子の養子縁組と、その本人・子孫の継承資格を示す図解。', [('kazuhi2024/2081201410503492037','法の下の平等との関係を問う','旧宮家の男系男子を対象にすることについて、憲法との関係を議論すべきだと問いかけています。'),('fi44504/2081220792025764197','養子による男系の維持を評価','旧宮家からの養子によって、男系の宮家を存続させる考えを支持しています。')]),
'princess-aiko': ('aiko-v3', '女性皇族の婚姻後の身分と、配偶者・子の扱いを示す図解。', [('so_far_away0712/2081023992228630655','現行の継承資格を重視','個人への支持と、法律で定める継承資格を分けて考える立場です。'),('Aruhuvrv0/2081152597432688720','女性皇族と子の地位を提案','女性皇族の婚姻後の皇籍維持に加え、その子も皇族とする解決策を提案しています。')]),
'legislative-process': ('shingi-v2', '皇室典範改正法の取りまとめから可決・公布までの流れを示す図解。', [('oaVVaHIYjJ2s8Y6/2081235016089309556','安定継承の議論を求める','安定的な皇位継承の議論を置いたまま決定が進んだことを批判しています。'),('dainankosan/2081237426488688766','議論の長期化を懸念','時間をかけること自体を評価する姿勢に異議を唱え、政策の停滞を懸念しています。')]),
'other': ('sonota', '複数の話題を整理する補助図です。「その他」は、今回案への「未表明」や「判断困難」と同じ分類ではありません。', [('77tMf5niwphliBQ/2081235258192904235','報道に多様な視点を求める','国会と新聞の論調の違いに違和感を示し、公平で多様な視点の報道を求めています。'),('fRdpHzPfSK70519/2081230489516720571','記事の受け取り方に異議','政治家への支持とは別に、記事に左右されることへの異議を述べています。')]),
}

def restore_issue_media(text, public):
    esc = html.escape
    cards = []
    for issue in public['issues']:
        iid = issue['id']; key = iid.removeprefix('koshitsu-tenpakai-')
        asset, note, posts = MEDIA[key]
        filename = 'koshitsu-vote-sonota.webp' if asset == 'sonota' else f'koshitsu-infographic-wide-{asset}.webp'
        url = '../../docs/images/topics/koshitsu-tenpakai/' + filename
        samples = ''
        for identity, label, summary in posts:
            user, post = identity.split('/')
            post_url = f'https://x.com/{user}/status/{post}'
            post_label = f'@{user} の投稿をXで見る'
            samples += (
                f'<div class="hermes-sample"><span class="hermes-sample-meta">{esc(label)}</span>'
                f'<blockquote class="twitter-tweet" data-conversation="none" data-dnt="true">'
                f'<a href="{post_url}">{post_label}</a></blockquote>'
                f'<div class="x-embed-fallback"><a href="{post_url}">{post_label}</a></div></div>'
            )
        cards.append(f'<article class="ic" id="issue-{iid}"><div class="ic-head"><h3>{esc(issue["label"])}</h3><span class="cnt">{issue["count"]}<small>件</small></span></div><figure><a href="{url}" target="_blank" rel="noopener"><img src="{url}" alt="{esc(issue["label"])}の論点図解" loading="lazy"></a><figcaption>{esc(note)}</figcaption></figure><div class="hermes-samples">{samples}</div><a class="ic-back" href="#planet-block">↑ 地図へ戻る</a></article>')
    block = '<section class="panel" id="issue-cards"><div class="panel-title"><h2>論点ごとの図解とX投稿</h2></div><p>投稿の要旨は編集部による要約です。各論点の考え方の例であり、今回案全体への賛否を表すものとは限りません。埋め込みが表示されない場合は、投稿リンクからXで確認できます。</p>' + ''.join(cards) + '</section>'
    text = text.replace('<!-- PLANET_SECTION_END -->', '<!-- PLANET_SECTION_END -->' + block, 1)
    text = text.replace('</head>', '<style>'+ ISSUE_CSS + '\n#issue-cards .hermes-samples{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-top:20px}#issue-cards .hermes-sample{min-width:0}#issue-cards figcaption{font-size:13px;line-height:1.8;margin-top:10px;color:#596174}#issue-cards .hermes-sample-meta{font-weight:800}#issue-cards .x-embed-fallback{margin:6px 0 0;font-size:12px}#issue-cards .x-embed-fallback a{color:var(--muted)}#issue-cards blockquote.twitter-tweet a{font-size:12px;color:var(--muted)}@media(max-width:640px){#issue-cards .hermes-samples{grid-template-columns:1fr}}</style></head>', 1)
    marker = 'if (extras) h += extras.innerHTML;'
    assert text.count(marker) == 1
    text = text.replace(marker, marker + '\n  h += \'<p><a class="go-card" href="#issue-\'+it.id+\'">この論点の図解とX投稿を見る ↓</a></p>\';')
    # Static fallback provides the same destination with JavaScript disabled.
    import re
    for issue in public['issues']:
        iid = issue['id']
        text, n = re.subn(r'(<section[^>]+id="fb-'+re.escape(iid)+r'"[^>]*>)', lambda m:m[0]+f'<p><a href="#issue-{iid}">この論点の図解とX投稿を見る ↓</a></p>', text, count=1)
        assert n == 1
    return text
