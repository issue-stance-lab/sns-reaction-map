"""Script-free complete reading/printing view derived from the verified page."""
from bs4 import BeautifulSoup

READ_PAGE = 'bukatsu-chiiki-full.html'
CSS = '''
.site-chrome,.mobile-bottom,.mobile-dock,.contents,.issue-tabs,.reason-index,.reason-menu,
.issue-next,.other-reason,.map-top,.map-shell,.map-caption,.map-tools,.mobile-issues,
.global-stances,.trend-stage,.trend-controls,.trend-tabs,.trend-share,
#vote-section,#reading-announcement,button,.prototype-banner{display:none!important}
.issue-panel,.reason-detail,[data-trend-panel]{display:block!important}
.reason-layout{display:block!important}.reason-detail{margin-bottom:32px;border-bottom:1px solid #ccd5df;padding-bottom:24px}
.static-guide{max-width:1116px;margin:24px auto;padding:20px;background:#eef5ff}
.static-guide nav{display:flex;flex-wrap:wrap;gap:12px 24px}.static-guide p{margin:8px 0}
.reason-detail>.eyebrow{font-size:13px}.issue-heading{break-after:avoid}
.issue-illustration img{max-height:320px;object-fit:contain}
@media print{
 @page{size:A4;margin:15mm}
 html{scroll-padding:0}body{font-size:10pt;line-height:1.6}
 .preview,.static-guide,.parity-footer,.hero-count,.issue-heading>a,.trend-detail-link{display:none!important}
 .hero h1{font-size:24pt!important}.hero-heading{display:block!important}
 .issue-panel{break-before:page}.issue-heading,.reason-detail h3{break-after:avoid}
 .reason-detail,.rich-content,details{break-inside:auto!important}
 .issue-glance{break-inside:avoid}.glance-svg-mobile{display:none!important}.glance-svg-desktop{display:block!important}
 .trend-table-wrap{overflow:visible!important}.trend-table{min-width:0!important;width:100%!important;font-size:8pt!important}
 table{border-collapse:collapse}thead{display:table-header-group}tr,img,svg{break-inside:avoid}
 img{max-width:100%!important}a{overflow-wrap:anywhere}h2{font-size:18pt!important}
}
'''

def readable(markup, page):
    s=BeautifulSoup(markup,'html.parser')
    for panel in s.select('[data-trend-panel]'):
        image=panel.select_one('.trend-share-item[data-variant="detail"] img')
        stage=panel.select_one('.trend-stage')
        if image and stage:
            image['style']='width:100%;height:auto;break-inside:avoid'
            stage.replace_with(image.extract())
    for menu in s.select('.reason-menu'):
        for node in menu.select('.redesign-coverage,.issue-stances'):
            menu.insert_before(node.extract())
    for group in s.select('.global-stances'):
        group.parent.decompose()
    for group in s.select('.original-posts,.issue-examples'):
        for node in group.select('.fine'):node.decompose()
    for node in s.select('script,noscript,iframe,.trend-stage,.trend-controls,.trend-tabs,.trend-share,#vote-section,.reason-menu,.another,.other-reason,.issue-next,.map-shell,.map-top,.map-caption,.map-tools,#mobile-issues,#issue-tabs,#reading-announcement,.global-stances'):
        node.decompose()
    for node in s.select('.issue-panel[hidden],.reason-detail[hidden],[data-trend-panel][hidden]'):
        del node['hidden']
    for node in s.select('details'):
        node.name='section'
        node.attrs.pop('open',None)
        summary=node.find('summary',recursive=False)
        if summary:summary.name='h3'

    for node in s.select('[onclick]'):del node['onclick']
    for node in s.select('img[loading]'):node['loading']='eager'
    for node in s.select('.issue-heading .eyebrow'):
        node.string=node.get_text().replace('選択中の論点','論点')
    for node in s.select('.reason-detail>.eyebrow'):
        node.string=node.get_text().replace('選んだ理由','理由')
    for node in s.select('meta[name="robots"]'):node.decompose()
    s.head.append(s.new_tag('meta',attrs={'name':'robots','content':'noindex,follow'}))
    s.title.string='部活動の地域移行：全文・印刷版｜SNS反応まっぷ'
    style=s.new_tag('style',id='readable-layout');style.string=CSS;s.head.append(style)
    guide=s.new_tag('div',attrs={'class':'static-guide'})
    p=s.new_tag('p');p.string='全文・印刷版。すべての論点と資料を続けて読めます。';guide.append(p)
    p=s.new_tag('p');p.string='印刷には、ブラウザの印刷メニューをご利用ください。';guide.append(p)
    back=s.new_tag('a',href=page);back.string='通常のページに戻る';guide.append(back)
    nav=s.new_tag('nav',attrs={'aria-label':'論点の目次'})
    for panel in s.select('.issue-panel'):
        a=s.new_tag('a',href='#'+panel['id']);a.string=panel.select_one('.issue-heading h2').get_text(' ',strip=True);nav.append(a)
    guide.append(nav);s.body.insert(0,guide)
    ids={node['id'] for node in s.select('[id]')}
    for a in s.select('a[href^="#"]'):
        if a['href'][1:] not in ids:a['href']=page+a['href']
    return str(s)
