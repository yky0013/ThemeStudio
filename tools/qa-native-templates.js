(async () => {
  let sequence = 300000;
  const pending=new Map(); const bridge=window.chrome.webview;
  bridge.addEventListener('message',({data})=>{const request=pending.get(data.id);if(!request)return;pending.delete(data.id);data.error?request.reject(new Error(data.error)):request.resolve(data.result);});
  const call=(operation,payload={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});bridge.postMessage({id,operation,payload});});
  const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const result={checks:[],errors:[]};let applied=false;
  const image=source=>new Promise((resolve,reject)=>{const img=new Image();const timeout=setTimeout(()=>reject(new Error('Image timeout: '+source)),8000);img.onload=()=>{clearTimeout(timeout);resolve({width:img.naturalWidth,height:img.naturalHeight});};img.onerror=()=>{clearTimeout(timeout);reject(new Error('Image failed: '+source));};img.src=source;});
  const loadVideo=source=>new Promise((resolve,reject)=>{const video=document.createElement('video');video.muted=true;video.preload='auto';const timeout=setTimeout(()=>finish(new Error('Video timeout')),10000);function finish(error){clearTimeout(timeout);video.removeAttribute('src');video.load();video.remove();error?reject(error):resolve(true);}video.onloadeddata=()=>finish();video.onerror=()=>finish(new Error('Video failed: '+source));video.src=source;document.body.append(video);});
  try{
    const before=await call('state');
    const packs=await fetch('/templates/catalog.json').then(response=>response.json());
    if(packs.length!==7)throw new Error('Expected 7 packs');
    for(const pack of packs){
      const preview=await call('templates.preview',{id:pack.id});
      const size=await image(preview.url);await image('/templates/'+pack.thumbnail);
      result.checks.push({template:pack.id,virtualHostImage:size,thumbnail:true});
    }
    const media=await call('wallpaper.example',{kind:'video'});await loadVideo(media.url);result.checks.push({virtualHostVideo:true});
    document.getElementById('workbench-parallax').scrollIntoView();await delay(750);
    const example=[...document.querySelectorAll('#workbench-parallax button')].find(button=>button.textContent.includes('示例图片'));
    if(example){example.click();await delay(900);}
    const previewImage=document.querySelector('#workbench-parallax img');
    if(!previewImage?.complete||!previewImage?.naturalWidth)throw new Error('Actual preview panel did not load');
    result.checks.push({previewPanel:true});
    const outcome=await call('templates.apply',{id:'wuthering-waves',icons:true,cursors:true});applied=true;
    const during=await call('wallpaper.status');
    if(!during.active||during.mode!=='static')throw new Error('Static wallpaper did not apply');
    const changed=await call('state');if(changed.cursors.version===before.cursors.version)throw new Error('Cursor settings did not change');
    await call('templates.restore');applied=false;
    const after=await call('state');
    if(after.cursors.version!==before.cursors.version)throw new Error('Cursor restore mismatch');
    if(JSON.stringify(after.shortcuts.map(row=>row.sha256))!==JSON.stringify(before.shortcuts.map(row=>row.sha256)))throw new Error('Shortcut restore mismatch');
    result.checks.push({apply:outcome,restoredCursors:true,restoredShortcuts:true});
    document.getElementById('workbench-templates').scrollIntoView();await delay(500);
  }catch(error){result.errors.push(String(error));}
  finally{if(applied){try{await call('templates.restore');result.checks.push({recovered:true});}catch(error){result.errors.push('Recovery: '+error);}}}
  result.passed=result.errors.length===0;await call('app.qa-complete',result);
})();
