// Real application source, isolated DOM/GA4 mock: never touches the production analytics stream.
const vm = require('node:vm');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const source = fs.readFileSync('docs/article-reason-journey.js', 'utf8');
function setup({article=null, referrer='', path='/bike-blue-ticket-reaction-map.html', host='sns-reaction-map.jp', visibility='visible', gtag=true}={}) {
  const events=[], listeners={}, rows=[], loc=new URL('https://'+host+path);
  let callback, disconnected=false;
  const document={referrer, visibilityState:visibility,
    body:{getAttribute:()=>article},
    addEventListener:(name, fn)=>listeners[name]=fn,
    querySelectorAll:()=>rows.map(row=>({querySelector:()=>row}))};
  let selected=true;
  const panel={hasAttribute:()=>selected, getAttribute:()=> 'bike-blue-ticket-infrastructure-first'};
  rows.push({closest:()=>panel});
  function IntersectionObserver(fn) { callback=fn; this.observe=()=>{}; this.disconnect=()=>{disconnected=true;}; }
  const window={IntersectionObserver, ...(gtag?{gtag:(...args)=>events.push(args)}:{})};
  vm.runInNewContext(source, {window, document, location:loc, URL, Set, IntersectionObserver});
  return {events, document, window, listeners, selected:v=>selected=v,
    visible:(ratio=.5)=>callback?.([{target:rows[0], isIntersecting:ratio>0, intersectionRatio:ratio}]),
    click:href=>listeners.click?.({target:{closest:()=>({href})}}), disconnected:()=>disconnected};
}
let r=setup({article:'bike-blue-ticket-unfair'});
r.click('https://sns-reaction-map.jp/bike-blue-ticket-reaction-map.html#issue-bike-blue-ticket-infrastructure-first');
assert.equal(r.events[0][1], 'article_reason_click');
r.click('https://sns-reaction-map.jp/bike-blue-ticket-reaction-map.html');
r.click('https://other.example/bike-blue-ticket-reaction-map.html#issue-bike-blue-ticket-infrastructure-first');
assert.equal(r.events.length,1);
const referrer='https://sns-reaction-map.jp/articles/bike-blue-ticket-unfair.html?tracking=discard';
r=setup({referrer});r.visible(.49);assert.equal(r.events.length,0);
r.selected(false);r.visible(.9);assert.equal(r.events.length,0);
r.selected(true);r.visible(.5);r.visible(.8);assert.equal(r.events.length,1);
assert.equal(r.events[0][1], 'article_reason_view');
assert.equal(r.events[0][2].page_referrer, referrer.split('?')[0]);
assert.ok(r.disconnected());
r=setup({referrer, visibility:'hidden'});r.visible(.8);assert.equal(r.events.length,0);
r.document.visibilityState='visible';r.listeners.visibilitychange();assert.equal(r.events.length,1);
for(const opts of [{referrer:''},{referrer:'https://other.example/articles/kobe-katsu.html'},
 {referrer:'https://sns-reaction-map.jp/articles/index.html'},
 {referrer:referrer+'&analytics_test=1'}, {referrer,path:'/bike-blue-ticket-reaction-map.html?analytics_test=1'},
 {referrer,host:'localhost'},{referrer,gtag:false}]) {
 const x=setup(opts);x.visible(1);assert.equal(x.events.length,0,JSON.stringify(opts));
}
r=setup({article:'kobe-katsu',path:'/articles/kobe-katsu.html?analytics_test=1'});
r.click('https://sns-reaction-map.jp/bukatsu-chiiki-reaction-map.html#issue-bukatsu-chiiki-hiyo');
assert.equal(r.events.length,0);
console.log('journey event semantics: OK (clicks, visibility, selection, dedupe, referrer, tests, host, gtag)');
