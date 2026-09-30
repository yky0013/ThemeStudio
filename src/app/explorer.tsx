// SPDX-License-Identifier: AGPL-3.0-or-later
import { useEffect, useRef, useState } from 'preact/hooks';
import type { DesktopClient } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts';
import cs from './templates.module.css';

interface ExplorerState { supported:boolean; build:number; available:boolean; loaded:boolean; enabled:boolean; theme:string; canRestore:boolean; choices:{id:string;label:string}[] }
export function ExplorerPanel({client,native}:{client:DesktopClient;native:boolean}) {
  const [state,setState]=useState<ExplorerState|null>(null);
  const [theme,setTheme]=useState('');
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  const running=useRef(false);
  const touched=useRef(false);
  const refresh=async()=>{
    const next=await client.call<ExplorerState>('explorer.state');setState(next);
    if(!touched.current)setTheme(next.theme||'MicaBar');
    return next;
  };
  useEffect(()=>{if(native)void refresh().catch(e=>setError(String(e)));},[native,client]);
  const run=async(action:'apply'|'restore'|'refresh')=>{
    if(running.current)return;running.current=true;setBusy(true);setError('');setMessage('');
    try {
      const next=action==='refresh'?await refresh():await client.call<ExplorerState>(`explorer.${action}`,{theme});
      setState(next);
      if(action==='restore'){touched.current=false;setTheme(next.theme||'MicaBar');}
      if(action==='apply')setMessage(next.loaded?'预设已启用，已检测到模组载入。请打开资源管理器查看。':'预设已启用，尚未检测到载入。请关闭并重新打开资源管理器窗口，然后刷新状态。');
      if(action==='restore')setMessage('已恢复上一次应用前的资源管理器预设和启用状态。');
      if(action!=='refresh')document.dispatchEvent(new CustomEvent('theme-studio-runtime-state'));
    }catch(e){setError(e instanceof Error?e.message:String(e));try{await refresh();}catch{}}
    finally{running.current=false;setBusy(false);}
  };
  return <section id="workbench-explorer" className={cs.library}>
    <div className={cs.heading}><div><p className={cs.eyebrow}>FILE EXPLORER</p><h2>文件资源管理器，也换个样子</h2><p>为 Windows 11 资源管理器选择云母、玻璃或简洁布局，调整标签栏、地址栏和命令栏。</p></div></div>
    <div className={cs.options}><label>外观预设 <select aria-label="资源管理器外观预设" value={theme} disabled={busy||!native||!state?.supported} onChange={e=>{touched.current=true;setTheme(e.currentTarget.value);}}>{(state?.choices||[{id:'MicaBar',label:'MicaBar'}]).filter(c=>c.id).map(c=><option key={c.id} value={c.id}>{c.label}</option>)}</select></label><button className={cs.apply} disabled={busy||!state?.supported||!state.available||!theme} onClick={()=>void run('apply')}>{busy?'正在处理…':'应用到资源管理器'}</button><button disabled={busy||!state?.canRestore} onClick={()=>void run('restore')}>恢复上一次外观</button><button disabled={busy||!native} onClick={()=>void run('refresh')}>刷新状态</button></div>
    <p className={cs.hint}>{state?`Windows build ${state.build} · ${!state.supported?'需要 Windows 11 22H2 或更新版本':!state.available?'运行组件不完整':state.enabled?`已启用 ${state.theme} · ${state.loaded?'已检测到载入':'等待资源管理器载入'}`:'尚未启用'}`:'请在桌面应用中使用'}</p>
    <p className={cs.footnote}>首次应用需要编译，可能需要一两分钟。各预设改变的区域不同，文件列表区域不保证随预设改变，也不包含角色背景图。实际效果取决于 Windows 版本；应用后可重新打开窗口查看。由 <a href="https://github.com/ramensoftware/windows-11-file-explorer-styling-guide" target="_blank" rel="noopener noreferrer">Windows 11 File Explorer Styler</a> 提供。</p>
    {message&&<p className={cs.success} role="status">{message}</p>}{error&&<p className={cs.error} role="alert">{error}</p>}
  </section>;
}
