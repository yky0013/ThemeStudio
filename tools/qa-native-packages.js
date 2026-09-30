// Native WebView2 QA against an isolated pre-imported library. No desktop changes.
(async()=>{
  let sequence=700000;
  const bridge=window.chrome.webview,pending=new Map();
  bridge.addEventListener('message',({data})=>{const item=pending.get(data.id);if(!item)return;pending.delete(data.id);data.error?item.reject(new Error(data.error)):item.resolve(data.result);});
  const call=(operation,payload={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});bridge.postMessage({id,operation,payload});});
  const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const wait=async(check,timeout=10000)=>{const end=Date.now()+timeout;while(!check()){if(Date.now()>end)throw new Error('Timed out waiting for UI');await delay(100);}};
  const result={checks:[],errors:[]};
  const loadImage=url=>new Promise((resolve,reject)=>{const image=new Image();const timer=setTimeout(()=>reject(new Error('Image timeout: '+url)),8000);image.onload=()=>{clearTimeout(timer);resolve(image.naturalWidth);};image.onerror=()=>{clearTimeout(timer);reject(new Error('Image failed: '+url));};image.src=url;});
  const asset=(pack,file)=>pack.assetBase+file.split('/').map(encodeURIComponent).join('/');
  try{
    const {packs}=await call('templates.list');
    if(packs.length!==12)throw new Error('Expected 10 builtins and 2 imported packs');
    for(const pack of packs.filter(pack=>pack.source==='imported')){
      await loadImage(asset(pack,pack.wallpaper));
      await loadImage(asset(pack,pack.thumbnail));
      for(const icon of Object.values(pack.icons))await loadImage(asset(pack,icon.file));
      const preview=await call('templates.preview',{id:pack.id,wallpaperMode:'static'});
      await loadImage(preview.url);
      result.checks.push({id:pack.id,name:pack.name,source:pack.source,poster:true,icons:Object.keys(pack.icons).length,nativePreview:true});
    }
    const motion=packs.find(pack=>pack.source==='imported'&&pack.animatedWallpaper);
    const video=document.createElement('video');video.muted=true;video.src=asset(motion,motion.animatedWallpaper);document.body.append(video);
    await video.play();await delay(600);
    if(!video.videoWidth||video.currentTime<=0)throw new Error('Imported video did not decode/play');
    result.checks.push({importedVideoDecoded:true,width:video.videoWidth,advanced:video.currentTime>0});
    video.pause();video.removeAttribute('src');video.load();video.remove();
    await wait(()=>document.querySelectorAll('#workbench-templates article').length===12);
    const updates=document.getElementById('workbench-updates');
    const state=await call('updates.state');
    if(state.currentVersion!=='0.4.1')throw new Error('Packaged backend version mismatch');
    updates.scrollIntoView();
    const check=[...updates.querySelectorAll('button')].find(button=>button.textContent==='检查更新');
    const offline=[...updates.querySelectorAll('button')].find(button=>button.textContent==='选择离线更新包');
    if(!check||check.disabled||!offline||offline.disabled)throw new Error('Native update controls unavailable');
    check.click();
    await wait(()=>!!updates.querySelector('[role=alert]'),40000);
    await wait(()=>!check.disabled);
    if(!/暂未提供可公开访问|无法连接更新源|限制了更新请求/.test(updates.textContent))throw new Error('Expected honest unavailable-source message');
    result.checks.push({version:state.currentVersion,updatesNativeControls:true,sourceErrorShown:updates.querySelector('[role=alert]')?.textContent});
    const card=[...document.querySelectorAll('#workbench-templates article')].find(card=>card.textContent.includes('纯静态 · 导入示例'));
    card.scrollIntoView();
    [...card.querySelectorAll('button')].find(button=>button.textContent==='查看预览').click();
    await wait(()=>!!document.querySelector('[role=dialog]'));
    const dialog=document.querySelector('[role=dialog]');
    const motionButton=[...dialog.querySelectorAll('button')].find(button=>button.textContent==='播放动态版');
    if(!motionButton.disabled||dialog.querySelector('video'))throw new Error('Static-only pack must disable motion');
    await wait(()=>[...dialog.querySelectorAll('img')].every(image=>image.complete&&image.naturalWidth));
    if(!dialog.textContent.includes('不含配套图标')||!dialog.textContent.includes('不含配套指针'))throw new Error('Optional accessories not represented');
    result.checks.push({cards:12,staticOnlyPreview:true,optionalAccessories:true,exportControl:!![...dialog.querySelectorAll('button')].find(button=>button.textContent==='导出完整套装')});
    if(document.documentElement.scrollWidth>window.innerWidth+1)throw new Error('Horizontal overflow');
    result.checks.push({width:window.innerWidth,height:window.innerHeight,noHorizontalOverflow:true});
  }catch(error){result.errors.push(String(error));}
  result.passed=result.errors.length===0;
  await call('app.qa-complete',result);
})();
