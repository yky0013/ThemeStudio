(async()=>{
  let sequence=920000;const pending=new Map();
  window.chrome.webview.addEventListener('message',({data})=>{const request=pending.get(data.id);if(!request)return;pending.delete(data.id);data.error?request.reject(new Error(data.error)):request.resolve(data.result);});
  const call=(operation,payload={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});window.chrome.webview.postMessage({id,operation,payload});});
  const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const until=async(predicate)=>{for(let n=0;n<400;n++){if(predicate())return;await pause(50);}throw new Error('UI condition timed out');};
  const result={checks:[],errors:[],explorerLiveApplyTested:false,cursorRoundtripTested:false};
  const button=text=>[...document.querySelectorAll('button')].find(b=>b.textContent.trim()===text);
  const ready=()=>!document.querySelector('[data-testid=apply-appearance]').disabled;
  async function stageCurrentCursor(){
    const control=document.querySelector('#workbench-cursors select[aria-label="指针大小"]');
    await until(()=>!control.matches(':disabled')&&!document.querySelector('#appearance-actions strong').textContent.includes('正在处理'));
    control.dispatchEvent(new Event('change',{bubbles:true}));await until(ready);
  }
  async function apply(){
    button('应用当前主题').click();
    await until(()=>document.querySelector('#appearance-actions [role=status]')?.textContent.includes('已应用'));
    await until(()=>!button('恢复上一次').disabled);
    if(document.querySelector('#appearance-actions [role=alert]'))throw new Error('Appearance apply reported an error');
  }
  try{
    await until(()=>document.querySelector('#workbench-cursors select[aria-label="指针大小"]'));
    const isolated=await call('appearance.state');const initialDesktop=await call('state');
    if(isolated.canUndo||isolated.canRestoreInitial||isolated.pending||initialDesktop.shortcuts.length)throw new Error('Expected a fresh, isolated QA profile');
    const controls=[...document.querySelectorAll('button')].map(b=>b.textContent.trim());
    if(controls.filter(t=>t==='应用当前主题').length!==1)throw new Error('Unified apply is not unique');
    if(controls.some(t=>t==='一键应用'||t==='应用图片外观'||t==='应用鼠标指针'||/^应用(动态|静态)版套装$/.test(t)))throw new Error('Legacy apply entry remains');
    if(!button('恢复上一次')||!button('恢复使用前外观'))throw new Error('Two recovery levels missing');
    result.checks.push({singleApplyEntry:true,twoRecoveryLevels:true});
    const {packs}=await call('templates.list');if(packs.length!==7)throw new Error('Unexpected catalog');
    document.querySelector('button[aria-label="预览鸣潮"]').click();await pause(100);
    const dialog=document.querySelector('[role=dialog]');
    [...dialog.querySelectorAll('button')].find(b=>b.textContent==='文件资源管理器').click();await pause(100);
    if(!dialog.querySelector('figure')?.textContent.includes('选择要预览的文件'))throw new Error('Preview pane missing');
    [...dialog.querySelectorAll('button')].find(b=>b.textContent==='选择并关闭预览').click();await until(ready);
    button('取消待应用').click();await pause(300);
    const trace=await call('app.qa-trace');
    if(trace.some(op=>/\.(apply|restore|begin)$/.test(op)))throw new Error('Selection or preview changed the system');
    result.checks.push({selectionPreviewOnly:true});
    // Use the already-current cursor artwork and size. The Python harness keeps
    // an independent raw registry snapshot and restores it even if this fails.
    await stageCurrentCursor();await apply();result.cursorRoundtripTested=true;
    button('恢复上一次').click();
    await until(()=>document.querySelector('#appearance-actions [role=status]')?.textContent.includes('已恢复上一次'));
    await until(()=>button('恢复上一次').disabled);
    await stageCurrentCursor();await apply();
    button('恢复使用前外观').click();
    await until(()=>document.querySelector('#appearance-actions [role=status]')?.textContent.includes('已恢复初始外观'));
    result.checks.push({nativeCombinedApply:true,nativeUndo:true,nativeInitialRestore:true});
    const state=await call('appearance.state');if(state.pending)throw new Error('A transaction was left pending');
    result.checks.push({recoveryState:state});
    document.getElementById('studio-content').style.scrollBehavior='auto';
    document.getElementById('workbench-explorer').scrollIntoView({behavior:'instant',block:'start'});await pause(150);
  }catch(error){result.errors.push(String(error));}
  result.passed=result.errors.length===0;await call('app.qa-complete',result);
})();
