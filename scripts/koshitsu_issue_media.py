"""Private candidate issue illustrations and publicly linked representative X posts."""
import html
from build_planet_page_preview import ISSUE_CSS

MEDIA = {
'patrilineal-matrilineal': ('keisho', '旧図解です。継承資格の変更を見送ったことと、今回の改正法の成立は別です。人数・伝統年数の表記は現状を検証した数値ではありません。', [('benjymin84/2081234225664262600','男系の継承を重視','女性天皇への否定とは分けて、男系の継承を続けたいと述べています。'),('a_aok04352/2080825663821615144','男女を問わない安定継承を求める','従来の仕組みを続ける難しさを挙げ、男女を問わず継承できる制度を求めています。')]),
'female-emperor': ('josei-tenno', '旧図解です。画像の支持率には出典の再確認が必要です。また、在位中の天皇を皇位継承順位に含める表記は誤りです。女性天皇と女系天皇は異なる概念です。', [('5VcfqTGE08SrXGE/2081146247327760862','女系への移行を懸念','結婚できる女性天皇が女系の継承につながることを懸念しています。'),('ayumuchan3/2081231595923734681','女性天皇となる可能性に言及','投稿者は、愛子さまの教育方針を、将来のさまざまな立場に備えるものと捉えています。')]),
'former-royal-adoption': ('yoshi', '制度案を議論していた時点の旧図解です。現在は改正後第三十八条を確認済みです。1947年から2026年までは79年で、画像の「80年以上」「未確定」は現状の説明ではありません。', [('kazuhi2024/2081201410503492037','法の下の平等との関係を問う','旧宮家の男系男子を対象にすることについて、憲法との関係を議論すべきだと問いかけています。'),('fi44504/2081220792025764197','養子による男系の維持を評価','旧宮家からの養子によって、男系の宮家を存続させる考えを支持しています。')]),
'princess-aiko': ('aiko', '旧図解です。「件数極少」は今回の集計を表しません。今回の改正では、婚姻後も皇族となる女性皇族の配偶者と子は皇族としない整理です。', [('so_far_away0712/2081023992228630655','現行の継承資格を重視','個人への支持と、法律で定める継承資格を分けて考える立場です。'),('Aruhuvrv0/2081152597432688720','女性皇族と子の地位を提案','女性皇族の婚姻後の皇籍維持に加え、その子も皇族とする解決策を提案しています。')]),
'legislative-process': ('shingi', '旧図解です。画像内の審議時間と主要法案の平均との比較は、根拠を再確認するまで確定した数値として扱いません。', [('oaVVaHIYjJ2s8Y6/2081235016089309556','安定継承の議論を求める','安定的な皇位継承の議論を置いたまま決定が進んだことを批判しています。'),('dainankosan/2081237426488688766','議論の長期化を懸念','時間をかけること自体を評価する姿勢に異議を唱え、政策の停滞を懸念しています。')]),
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
            samples += f'<div class="hermes-sample"><span class="hermes-sample-meta">{esc(label)}</span><p class="hermes-sample-summary">{esc(summary)}</p><blockquote class="twitter-tweet" data-conversation="none" data-dnt="true"><a href="https://x.com/{user}/status/{post}">@{user} の投稿をXで見る</a></blockquote></div>'
        cards.append(f'<article class="ic" id="issue-{iid}"><div class="ic-head"><h3>{esc(issue["label"])}</h3><span class="cnt">{issue["count"]}<small>件</small></span></div><figure><a href="{url}" target="_blank" rel="noopener"><img src="{url}" alt="{esc(issue["label"])}の既存図解" loading="lazy"></a><figcaption>{esc(note)}</figcaption></figure><div class="hermes-samples">{samples}</div><a class="ic-back" href="#planet-block">↑ 地図へ戻る</a></article>')
    block = '<section class="panel" id="issue-cards"><div class="panel-title"><h2>論点ごとの図解とX投稿</h2></div><p>投稿の要旨は編集部による要約です。各論点の考え方の例であり、今回案全体への賛否を表すものとは限りません。埋め込みが表示されない場合は、投稿リンクからXで確認できます。</p>' + ''.join(cards) + '</section>'
    text = text.replace('<!-- PLANET_SECTION_END -->', '<!-- PLANET_SECTION_END -->' + block, 1)
    text = text.replace('</head>', '<style>'+ ISSUE_CSS + '\n#issue-cards .hermes-samples{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-top:20px}#issue-cards .hermes-sample{min-width:0}#issue-cards figcaption{font-size:13px;line-height:1.8;margin-top:10px;color:#596174}#issue-cards .hermes-sample-meta{font-weight:800}@media(max-width:640px){#issue-cards .hermes-samples{grid-template-columns:1fr}}</style></head>', 1)
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
