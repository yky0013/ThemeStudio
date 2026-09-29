// SPDX-License-Identifier: AGPL-3.0-or-later
import { useEffect, useRef, useState } from 'preact/hooks';
import type { DesktopClient } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts';
import { version } from '../../package.json';
import cs from './templates.module.css';

interface Prepared { id:string; version:string; name:string; size:number; sha256:string; source:string }
interface Update { currentVersion:string; latestVersion:string; available:boolean; notes:string; size?:number }
interface Progress { stage:string; received:number; total:number }
export function UpdatePanel({client,native}:{client:DesktopClient;native:boolean}) {
  const [current,setCurrent]=useState(version);
  const [update,setUpdate]=useState<Update|null>(null);
  const [prepared,setPrepared]=useState<Prepared|null>(null);
  const [busy,setBusy]=useState('');
  const [progress,setProgress]=useState<Progress|null>(null);
  const [error,setError]=useState('');
  const [message,setMessage]=useState('');
  const running=useRef(false);
  useEffect(()=>{
    let alive=true;
    if(native)void client.call<{currentVersion:string;prepared:Prepared|null}>('updates.state').then(state=>{if(alive){setCurrent(state.currentVersion);setPrepared(state.prepared);}}).catch(failure=>{if(alive)setError(String(failure));});
    const handler=(event:Event)=>setProgress((event as CustomEvent<Progress>).detail);
    document.addEventListener('theme-studio-update-progress',handler);
    return()=>{alive=false;document.removeEventListener('theme-studio-update-progress',handler);};
  },[client,native]);
  const run=async(key:string,action:()=>Promise<void>)=>{
    if(running.current)return;
    running.current=true;setBusy(key);setError('');setMessage('');setProgress(null);
    try{await action();}catch(failure){setError(failure instanceof Error?failure.message:String(failure));}
    finally{running.current=false;setBusy('');}
  };
  return <section id="workbench-updates" className={`${cs.library} ${cs.updatePanel}`}>
    <div className={cs.heading}><div><p className={cs.eyebrow}>THEME STUDIO · UPDATES</p><h2>应用更新</h2><p>当前版本 v{current} · 更新后保留已导入的套装、素材与恢复记录。</p></div><div className={cs.toolbar}><button disabled={!native||!!busy} onClick={()=>void run('check',async()=>{setUpdate(null);const result=await client.call<Update>('updates.check');setUpdate(result);if(!result.available)setMessage(`没有可用的新版本。发布源最新正式版为 v${result.latestVersion}。`);})}>{busy==='check'?'正在检查…':'检查更新'}</button><button disabled={!native||!!busy} onClick={()=>void run('local',async()=>{const result=await client.call<Prepared|null>('updates.local');if(result){setPrepared(result);setMessage(`v${result.version} 安装包已校验，可以启动安装。`);}})}>{busy==='local'?'正在校验…':'选择离线更新包'}</button></div></div>
    <p className={cs.footnote}>在线更新从项目 GitHub 正式发布获取。离线更新请选择安装程序，并将配套的 .exe.sha256 文件放在同一文件夹。</p>
    {!native&&<p className={cs.footnote}>请在桌面应用中检查和安装更新。</p>}
    {update?.available&&<div className={cs.updateCard}><strong>新版本 v{update.latestVersion}</strong><p>{update.size?`${(update.size/1024/1024).toFixed(1)} MB · `:''}下载后校验完整性，再由你启动安装。</p>{update.notes&&<details><summary>查看更新说明</summary><p className={cs.releaseNotes}>{update.notes}</p></details>}<button className={cs.apply} disabled={!!busy} onClick={()=>void run('download',async()=>{const result=await client.call<Prepared>('updates.download',{version:update.latestVersion});setPrepared(result);setMessage('下载完成，安装包校验通过。');})}>{busy==='download'?'正在下载…':prepared?.version===update.latestVersion?'重新下载':'下载更新'}</button></div>}
    {(busy==='download'||busy==='local')&&<div role="status" className={cs.downloadProgress}><progress max={progress?.total||1} value={progress?.received||0}/><span>{progress?.stage==='verify'?'正在校验安装包…':progress?`${(progress.received/1024/1024).toFixed(1)} / ${(progress.total/1024/1024).toFixed(1)} MB`:'正在准备…'}</span>{busy==='download'&&<button onClick={()=>{void client.call('updates.cancel').catch(failure=>setError(String(failure)));setMessage('正在取消，请稍候…');}}>取消下载</button>}</div>}
    {prepared&&<div className={cs.updateCard}><strong>v{prepared.version} 已准备好安装</strong><p>{prepared.source} · SHA-256 已校验</p><p>点击后关闭主题工作室并打开安装向导。按向导完成更新后重新启动应用。</p><button className={cs.apply} disabled={!!busy} onClick={()=>void run('install',async()=>{await client.call('updates.install',{id:prepared.id});setMessage('安装向导已启动。');})}>{busy==='install'?'正在启动…':'关闭应用并启动安装'}</button></div>}
    {message&&<p role="status" className={cs.success}>{message}</p>}{error&&<p role="alert" className={cs.error}>{error}</p>}
  </section>;
}
