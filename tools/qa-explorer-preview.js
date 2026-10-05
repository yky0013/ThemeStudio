(async () => {
  let sequence=910000; const pending=new Map();
  window.chrome.webview.addEventListener('message',({data})=>{const p=pending.get(data.id);if(!p)return;pending.delete(data.id);data.error?p.reject(new Error(data.error)):p.resolve(data.result);});
  const call=(operation,payload={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});window.chrome.webview.postMessage({id,operation,payload});});
  const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const result={checks:[],errors:[],nativeSystemApplyTested:false};
  try {
    const {packs}=await call('templates.list');
    if(packs.length!==7||packs.some(p=>['zenless-zone-zero','arknights','blue-archive'].includes(p.id)))throw new Error('Retired built-ins still exposed');
    result.checks.push({sevenPacks:true,retiredPacksAbsent:true});
    const state=await call('explorer.state');
    if(!state.image||state.image.active)throw new Error('Unexpected fresh Explorer state');
    const image=document.querySelector('#workbench-explorer figure img');
    if(!image)throw new Error('Explorer preview image missing');
    await image.decode();
    const chooser=document.querySelector('#workbench-explorer select');
    chooser.value='chiikawa';chooser.dispatchEvent(new Event('change',{bubbles:true}));await pause(200);
    await document.querySelector('#workbench-explorer figure img').decode();
    if(!document.querySelector('#workbench-explorer figure img').src.includes('chiikawa/'))throw new Error('Theme preview did not change');
    const slider=document.querySelector('#workbench-explorer input[type=range]');
    slider.value='55';slider.dispatchEvent(new Event('input',{bubbles:true}));await pause(100);
    if(document.querySelector('#workbench-explorer figure img').style.opacity!=='0.55')throw new Error('Opacity preview did not change');
    result.checks.push({liveThemeSelection:true,liveOpacity:true});
    const windowPreview=image.parentElement;
    const pane=windowPreview.querySelector('aside:last-of-type');
    const status=windowPreview.lastElementChild;
    for(const element of [pane,status,...windowPreview.querySelectorAll('aside')]) {
      if(getComputedStyle(element).backgroundColor!=='rgba(0, 0, 0, 0)')throw new Error('Idle preview surface has an opaque background');
    }
    result.checks.push({idlePaneAndStatusTransparent:true});

    document.querySelector('button[aria-label="预览鸣潮"]').click();await pause(100);
    const dialog=document.querySelector('[role=dialog]');
    [...dialog.querySelectorAll('button')].find(b=>b.textContent==='文件资源管理器').click();await pause(100);
    if(!dialog.querySelector('figure[aria-label="鸣潮资源管理器效果预览"]'))throw new Error('Theme modal Explorer preview missing');
    const opacity=dialog.querySelector('input[aria-label="主题资源管理器背景可见度"]');
    opacity.value='42';opacity.dispatchEvent(new Event('input',{bubbles:true}));await pause(100);
    if(dialog.querySelector('figure img').style.opacity!=='0.42')throw new Error('Modal opacity preview did not change');
    result.checks.push({themeModalPreview:true,themeDefaultLinksExplorer:dialog.querySelector('input[type=checkbox]').checked});
    dialog.querySelector('button[aria-label="关闭预览"]').click();await pause(100);
    chooser.value='wuthering-waves';chooser.dispatchEvent(new Event('change',{bubbles:true}));
    slider.value='35';slider.dispatchEvent(new Event('input',{bubbles:true}));await pause(100);
    document.getElementById('studio-content').style.scrollBehavior='auto';
    document.getElementById('workbench-explorer').scrollIntoView({behavior:'instant',block:'start'});await pause(250);
    const trace=await call('app.qa-trace');
    const forbidden=trace.filter(op=>/\.(apply|restore|stop|install|launch|remove)$/.test(op));
    if(forbidden.length)throw new Error('Preview triggered mutations: '+forbidden.join(','));
    result.checks.push({previewReadOnly:true,operations:trace});
  } catch(error) { result.errors.push(String(error)); }
  result.passed=result.errors.length===0;
  await call('app.qa-complete',result);
})();
