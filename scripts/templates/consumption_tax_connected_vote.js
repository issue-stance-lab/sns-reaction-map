(function(){
  var TOPIC='consumption-tax-cut-issue-stance-v1';
  var STORAGE_KEY='sns_vote_'+TOPIC+'_my';
  var VOTE_ISSUES=[
    __ISSUES__
  ];
  var STANCES=[
    __STANCES__
  ];
  var CHOICES=__CHOICES__;
  var selectedIssue=null;
  var step1=document.getElementById('vote-step1'),step2=document.getElementById('vote-step2'),result=document.getElementById('vote-result');
  var issueBtns=document.getElementById('vote-issue-btns'),stanceBtns=document.getElementById('vote-stance-btns');
  function showVote(issue,stance){
    selectedIssue=issue.id;step1.style.display='none';step2.style.display='none';result.style.display='block';
    document.getElementById('vote-position-label').textContent='論点：'+issue.k+'　賛否：'+stance.k;
    document.getElementById('vote-position-text').textContent=issue.desc;
    var text='消費税減税、私が最も気になる論点は「'+issue.k+'」。'+stance.k+'の立場です。';
    document.getElementById('share-x').href='https://x.com/intent/tweet?text='+encodeURIComponent(text)+'&url='+encodeURIComponent('https://sns-reaction-map.jp/consumption-tax-cut-reaction-map.html');
  }
  VOTE_ISSUES.forEach(function(issue){
    var button=document.createElement('button');button.type='button';button.className='vote-issue-btn';button.dataset.voteIssue=issue.id;
    button.innerHTML='<span class="vote-issue-icon">'+issue.icon+'</span><span class="vote-issue-title">'+issue.k+'</span>';
    button.onclick=function(){selectedIssue=issue.id;step1.style.display='none';step2.style.display='block';};issueBtns.appendChild(button);
  });
  STANCES.forEach(function(stance){
    var button=document.createElement('button');button.type='button';button.className='vote-stance-btn';button.dataset.voteStance=stance.id;
    button.style.setProperty('--stance-color',stance.color);button.style.setProperty('--stance-bg',stance.bg);button.style.setProperty('--stance-shadow',stance.shadow);
    button.innerHTML='<span class="vs-icon">'+stance.icon+'</span><span class="vs-title">'+stance.k+'</span><span class="vs-desc">'+stance.desc+'</span>';
    button.onclick=async function(){
      var issue=VOTE_ISSUES.find(function(i){return i.id===selectedIssue;});if(!issue)return;
      var buttons=stanceBtns.querySelectorAll('button');buttons.forEach(function(b){b.disabled=true;});
      try{
        var response=await VoteStore.cast({topicId:TOPIC,choiceIdx:CHOICES[issue.id][stance.id],storageKey:STORAGE_KEY,localValue:{issueIdx:issue.slot,stanceIdx:stance.slot}});
        if(response.duplicate)alert('24時間以内にすでに投票されています。前回の投票が集計されています。');
        showVote(issue,stance);
      }catch(error){console.error('Vote request failed:',error);alert(VoteStore.friendlyError(error));}
      finally{buttons.forEach(function(b){b.disabled=false;});}
    };stanceBtns.appendChild(button);
  });
  document.getElementById('vote-redo-btn').onclick=function(){
    VoteStore.clear(STORAGE_KEY);selectedIssue=null;step1.style.display='block';step2.style.display='none';result.style.display='none';
  };
  if(VoteStore.isRemote())document.getElementById('vote-redo-btn').style.display='none';
  try{
    var previous=JSON.parse(localStorage.getItem(STORAGE_KEY)||'null');
    var issue=previous && VOTE_ISSUES.find(function(i){return i.slot===previous.issueIdx;});
    var stance=previous && STANCES.find(function(s){return s.slot===previous.stanceIdx;});
    if(issue && stance)showVote(issue,stance);
  }catch(_){localStorage.removeItem(STORAGE_KEY);}
})();
