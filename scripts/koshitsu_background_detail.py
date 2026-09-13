"""Source-grounded expansion and coordinated palette for the private candidate."""
from html import escape

REPORT='https://www.cas.go.jp/jp/seisaku/taii_tokurei/pdf/houkoku_honbun_20211222.pdf'
LAW='https://laws.e-gov.go.jp/api/2/law_data/322AC0000000003_20261024_508AC0000000066'
SECTIONS=[
('人数が減ると、どの役割に影響するのか',[
'出発点は、2017年の退位特例法に付された国会の決議です。安定的な皇位継承や女性宮家の創設などを政府が検討し、国会へ報告するよう求めました。2021年の有識者会議は、この要請を受けて議論しています。',
'報告書は、次の天皇を決める問題に加え、天皇の活動を支える皇族が将来もいるかという問題を挙げています。海外訪問などで天皇が不在のときの国事行為の臨時代行、皇室の身分に関する事項を審議する皇室会議、不測の事態での摂政などは、皇族が担う制度上の役割です。',
'さらに、災害の被災地への慰問、慰霊、国際親善、文化・学術・スポーツに関わる活動があります。報告書が皇族数の確保を急ぐ理由は、こうした活動と制度を支える人が減ることにあります。'],REPORT,'有識者会議報告書・1、6〜9ページ'),
('検討された3案と、今回の改正が選んだ範囲',[
'報告書は、①女性皇族が結婚後も身分を保つ、②皇統に属する男系の男子を養子に迎える、③養子縁組を経ず法律で直接皇族にする、という3案を示しました。③は、①と②だけでは十分な皇族数を確保できない場合に検討すべき案として位置付けています。',
'今回の改正が設けるのは①と②の仕組みです。結婚による身分離脱の規定を削り、養子によって皇族となる例外を新設します。一方、皇位継承資格を男系の男子に限る第一条は変えていません。「皇族を増やす改正」と「継承資格を広げる改正」を同じものとして読むと、議論の違いを見落とします。'],REPORT,'有識者会議報告書・9〜13ページ'),
('女性皇族が残ることと、家族の身分',[
'女性皇族が婚姻後も身分を保持すれば、それまで担ってきた活動を継続できます。報告書は、この利点とともに、子の継承資格を通じて女系継承につながるのではないかという反対意見も記しています。',
'その整理として報告書が示したのは、配偶者と子は皇族とせず、一般国民としての権利・義務を保つ考え方です。改正後の第十五条でも、女性皇族との婚姻を理由に配偶者が皇族になる仕組みは設けられていません。',
'制度が変わる当事者への配慮も課題です。現在の女性皇族は、婚姻すれば皇室を離れる制度を前提に人生を過ごしてきました。報告書は、その事情に十分留意する必要があるとしています。身分を残す効果だけでなく、本人の人生や家族との生活をどう支えるかまで含む論点です。'],REPORT,'有識者会議報告書・10〜11ページ'),
('養子制度は、誰でも皇族になれる仕組みではない',[
'改正後の第三十八条は、養子を迎える皇族から皇嗣と皇嗣妃を除き、皇室会議の議を経ることを求めています。対象は、現行皇室典範の下で皇族男子だった者の嫡男系嫡出の子孫に当たる、現に皇族でない男子です。さらに十五歳以上で、配偶者と子がいないことが条件です。',
'養子となる本人は縁組の時から皇族になりますが、第二条の皇位継承順序は適用されません。一方、その子孫については、養親ではなく実方の系統によって第二条などを適用します。皇族の人数を増やす効果と、次の世代の継承資格に及ぶ効果は、分けて考える必要があります。'],LAW,'改正後の皇室典範・第三十八条第一、三、四、六項'),
('資料が挙げる期待と、なお残る課題',[
'養子案について、報告書は直系の男子を得なければならないという重圧を和らげる可能性を挙げています。同時に、長年一般国民として暮らしてきた方々を迎えることや、現在の皇室との男系の血縁が遠いことから、国民の理解を得るのは難しいという意見も記しています。',
'報告書は、養子となった方が皇室の活動を担う中で理解と共感が育つことを期待しています。ただし、これは制度設計時の見通しです。具体的に誰が応じるのか、どれだけ皇族数を確保できるのか、当事者の負担が軽くなるのかは、この資料から実績として確認できることではありません。'],REPORT,'有識者会議報告書・11〜12ページ'),
]

def expand_background(text):
    paragraphs=[]
    for title,body,url,label in SECTIONS:
        paragraphs.append('<div class="bg-detail"><h3>'+escape(title)+'</h3>'+''.join('<p>'+escape(p)+'</p>' for p in body)+'<p class="bg-source">出典：<a href="'+url+'" target="_blank" rel="noopener">'+escape(label)+'</a>'+(' ／ <a href="'+LAW+'" target="_blank" rel="noopener">改正後の条文</a>' if title.startswith(('検討','女性')) else '')+'</p></div>')
    needle='<h3>なぜ始まったか</h3>'
    start=text.index(needle);end=text.index('<h3>これまでの経緯</h3>',start)
    text=text[:start]+''.join(paragraphs)+text[end:]
    # Preserve stance meanings: unexpressed remains a distinct, muted blue.
    text=text.replace('#8B9199','#69869C')
    text=text.replace('#planet-block .chart-box svg rect:first-of-type{fill:#DCE9F7}', '#planet-block .chart-box svg > rect:first-of-type{fill:#E4EEF2}')
    style='''<style>
#planet-block .chart-box,#planet-block .dotbox{background:#F7F9FA;border-color:#DCE5E8}
#planet-block .chart-box svg #seacover{fill:#F7F9FA}
#planet-block .chart-box svg .hill-hit{fill:transparent}
#planet-block .chart-box svg line[stroke="#2b3440"]{stroke:#E1E8EC}
#planet-block .chart-box svg line[stroke="#5b9bf0"][stroke-width="1.6"]{stroke:#69869C}
#planet-block .chart-box svg #seafloor path[fill="#122642"]{fill:#E4EEF2;stroke:#8CA9B6}
#planet-block .axis-note{background:#EDF3F5!important;border-left-color:#69869C!important}
#bukatsu-background .bg-source{font-size:12px;color:var(--muted);margin-top:8px}
#bukatsu-background .bg-detail{margin:24px 0;border-bottom:1px solid var(--line);padding-bottom:12px}
#bukatsu-background .bg-source a{color:inherit}
</style>'''
    text=text.replace('</body>',style+'</body>',1)
    # The saved article says no current spouse; it does not prohibit all marriage history.
    text=text.replace('十五歳以上で、婚姻歴がなく、子を持たないことが条件です。','十五歳以上で、配偶者と子がいないことが条件です。')
    return text
