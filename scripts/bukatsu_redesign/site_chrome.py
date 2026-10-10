from bs4 import BeautifulSoup
from pathlib import Path

def add_site_chrome(markup,root):
 s=BeautifulSoup(markup,'html.parser')
 nav='<a href="https://sns-reaction-map.jp/#topics">テーマ一覧</a><a href="https://sns-reaction-map.jp/#featured-questions">注目の問い</a><a href="https://sns-reaction-map.jp/about.html">データについて</a><a href="https://sns-reaction-map.jp/usage.html">使い方</a><a href="https://sns-reaction-map.jp/usage.html#faq">よくある質問</a>'
 header=BeautifulSoup('<div class="site-chrome"><header class="global-header"><a class="global-logo" href="https://sns-reaction-map.jp/">SNS反応まっぷ</a><nav class="global-desktop" aria-label="サイトの案内">'+nav+'</nav><a class="global-cta" href="https://sns-reaction-map.jp/#topics">テーマを見る</a><details class="global-mobile"><summary>メニュー</summary><nav aria-label="サイトの案内（スマホ）">'+nav+'</nav></details></header><div class="reading-progress" id="reading-progress"><span>読んだところ</span><div class="reading-segments" aria-hidden="true"></div><b class="reading-count" role="status" aria-live="polite"></b><span class="reading-help">論点や資料を開くと増えます</span></div></div>','html.parser')
 s.select_one('.site-head').replace_with(header)
 style=s.new_tag('style');style.string=(root/'.build/site_chrome.css').read_text();s.head.append(style)
 script=s.new_tag('script');script.string=(root/'.build/site_chrome.js').read_text();s.body.append(script)
 return str(s)
