import json,re
from bs4 import BeautifulSoup
def decorate(html, app):
    s=BeautifulSoup(html,'html.parser')
    icons=json.loads(re.search(r'const topicIcons=(\[.*?\]);',app).group(1))
    colors=['#008b92','#dc6256','#2177be','#aa7500','#008d86','#7650b4','#1e79c6']
    pales=['#eaf8f7','#fff0ed','#edf5ff','#fff8dc','#eaf7f3','#f3eefb','#edf7ff']
    def icon(path):
        return '<svg class="picto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+path+'</svg>'
    doc=icon('<path d="M5 2h9l5 5v15H5ZM14 2v6h5M8 12h8M8 16h8"/>')
    search=icon('<circle cx="10" cy="10" r="7"/><path d="m15 15 7 7"/>')
    clock=icon('<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/>')
    chart=icon('<path d="M3 3v18h19M6 15l5-5 4 3 6-8"/>')
    def prepend(node,svg):
        if node: node.insert(0,BeautifulSoup('<span class="lower-icon">'+svg+'</span>','html.parser'))
    def theme(node,i):
        node['style']='--topic:'+colors[i]+';--topic-pale:'+pales[i]
    prepend(s.select_one('.comparison .section-title h2'),icons[5])
    for row,i in zip(s.select('.compare-row'),[0,4,2]):
        theme(row,i);prepend(row.select_one('h3'),icons[i])
    prepend(s.select_one('.reading-title'),search)
    for i,panel in enumerate(s.select('.issue-panel')):
        theme(panel,i)
        prepend(panel.select_one('.issue-heading h2'),icons[i])
        prepend(panel.select_one('.reason-index h3'),icons[5])
        for h in panel.select('.reason-detail > h3'): prepend(h,icons[5])
        for h in panel.select('.another h4'): prepend(h,icons[5])
        prepend(panel.select_one('.source-intro h3'),doc)
        for summary in panel.select('.original-posts > summary,.issue-examples > summary'): prepend(summary,icons[5])
    prepend(s.select_one('.deep-read > h2'),doc)
    details=s.select('.deep-read > details')
    for n,d in enumerate(details):
        i=[1,6,5,0,2,4][n%6];theme(d,i)
        svg={'background':clock,'local':icons[6],'source-only':doc,'trends':chart,'classroom':icons[2],'method':search}.get(d.get('id'),doc)
        prepend(d.select_one('summary'),svg)
    return str(s)
