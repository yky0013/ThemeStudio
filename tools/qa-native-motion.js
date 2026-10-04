// Run with the diagnostic host and an isolated --smoke-dir. Fixture media IDs
// are prepended by tools/qa-motion.ps1, never accepted from the product UI.
(async () => {
  let sequence=700000;
  const pending=new Map(), bridge=window.chrome.webview;
  bridge.addEventListener('message',({data})=>{const entry=pending.get(data.id);if(!entry)return;pending.delete(data.id);data.error?entry.reject(new Error(data.error)):entry.resolve(data.result);});
  const call=(operation,payload={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});bridge.postMessage({id,operation,payload});});
  const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const result={checks:[],errors:[]};let templates=0,loose=false;
  const settings={enabled:false,preset:'elegance',strength:1,perspective:false,tilt:0,opposite:true};
  const playing=state=>state.active&&state.windows?.length&&state.windows.every(w=>w.attached&&w.playing);
  const load=async source=>{
    const video=document.createElement('video');video.muted=true;video.src=source;document.body.append(video);
    try{await video.play();await delay(250);if(video.videoWidth!==1920||video.duration!==12||video.currentTime<=0)throw new Error('Video playback mismatch');}
    finally{video.pause();video.removeAttribute('src');video.load();video.remove();}
  };
  try{
    const packs=await fetch('/templates/catalog.json').then(r=>r.json());
    if(packs.length!==7)throw new Error('Expected 7 motion packs');
    for(const pack of packs){const media=await call('templates.preview',{id:pack.id,wallpaperMode:'animated'});await load(media.url);result.checks.push({clip:pack.id,decoded:true,advancing:true});}
    const first=await call('templates.apply',{id:packs[0].id,icons:false,cursors:false,wallpaperMode:'animated'});templates++;
    let status=await call('wallpaper.status');const motionId=status.media.id;
    if(first.mode!=='animated'||!playing(status))throw new Error('Template did not play on desktop');
    status=await call('wallpaper.pause',{paused:true});if(!status.paused||status.windows.some(w=>w.playing))throw new Error('Pause failed');
    status=await call('wallpaper.pause',{paused:false});if(!playing(status))throw new Error('Resume failed');
    await call('templates.apply',{id:packs[1].id,icons:false,cursors:false,wallpaperMode:'static'});templates++;
    status=await call('wallpaper.status');if(!status.active||status.mode!=='static')throw new Error('Static mode did not release the renderer');
    await call('templates.restore');templates--;
    status=await call('wallpaper.status');if(!playing(status)||status.media.id!==motionId)throw new Error('Previous animated template did not resume');
    await call('templates.restore');templates--;
    result.checks.push({dynamicToStatic:true,restorePreviousAnimation:true,pauseResume:true});
    for(const fixture of qaAnimatedFiles){
      status=await call('wallpaper.apply',{mediaId:fixture.id,settings});loose=true;
      if(status.media.kind!=='image'||!status.media.animated||!playing(status))throw new Error('Animated image flattened: '+fixture.format);
      status=await call('wallpaper.pause',{paused:true});if(status.windows.some(w=>w.playing))throw new Error('Image pause failed');
      status=await call('wallpaper.pause',{paused:false});if(!playing(status))throw new Error('Image resume failed');
      await call('wallpaper.stop');loose=false;
      result.checks.push({format:fixture.format,animatedWithoutParallax:true,pauseResume:true});
    }
    const state=await call('runtime.state');
    if(!['windows','mac','custom'].includes(state.desktopMode))throw new Error('Desktop mode state missing');
    result.checks.push({desktopModeReported:state.desktopMode,liveMacSwitch:'not run: requires administrator'});
    document.getElementById('workbench-desktop-mode').scrollIntoView();await delay(350);
  }catch(error){result.errors.push(String(error));}
  finally{
    if(loose){try{await call('wallpaper.stop');}catch(error){result.errors.push('Stop: '+error);}}
    while(templates>0){try{await call('templates.restore');templates--;}catch(error){result.errors.push('Restore: '+error);break;}}
  }
  result.passed=result.errors.length===0;await call('app.qa-complete',result);
})();
