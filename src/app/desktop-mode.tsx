// SPDX-License-Identifier: AGPL-3.0-or-later
import { useEffect, useRef, useState } from 'preact/hooks';
import { useTranslation } from 'react-i18next';
import type { DesktopClient } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts';
import type { RuntimeState } from './runtime.tsx';
import cs from './templates.module.css';

export function DesktopModePicker({client,native}:{client:DesktopClient;native:boolean}) {
  const {i18n}=useTranslation();
  const en=i18n.language==='en';
  const [state,setState]=useState<RuntimeState|null>(null);
  const [selected,setSelected]=useState<'windows'|'mac'>('windows');
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [message,setMessage]=useState('');
  const running=useRef(false);
  const touched=useRef(false);
  useEffect(()=>{
    let alive=true;
    const refresh=()=>{if(native)void client.call<RuntimeState>('runtime.state').then(next=>{
      if(alive){setState(next);if(!touched.current)setSelected(next.desktopMode==='mac'?'mac':'windows');}
    }).catch(failure=>{if(alive)setError(String(failure));});};
    const changed=(event:Event)=>{const next=(event as CustomEvent<RuntimeState>).detail;if(next){setState(next);if(!touched.current)setSelected(next.desktopMode==='mac'?'mac':'windows');}else refresh();};
    refresh();document.addEventListener('theme-studio-runtime-state',changed);
    return()=>{alive=false;document.removeEventListener('theme-studio-runtime-state',changed);};
  },[client,native]);
  const apply=async()=>{
    if(running.current)return;
    running.current=true;setBusy(true);setError('');setMessage('');
    try{
      const next=await client.call<RuntimeState>('runtime.desktop.apply',{mode:selected});
      setState(next);touched.current=false;
      document.dispatchEvent(new CustomEvent('theme-studio-runtime-state',{detail:next}));
      setMessage(en?`Applied ${selected==='mac'?'Mac style':'Windows'} desktop.`:`已切换到 ${selected==='mac'?'Mac 风格':'Windows'} 桌面。`);
    }catch(failure){setError(failure instanceof Error?failure.message:String(failure));}
    finally{running.current=false;setBusy(false);}
  };
  return <section id="workbench-desktop-mode" className={`${cs.library} ${cs.modeSection}`}>
    <div className={cs.heading}><div><p className={cs.eyebrow}>YOUR DESKTOP, YOUR WAY</p><h2>{en?'Choose your desktop style':'先选一种桌面风格'}</h2><p>{en?'Pair either layout with any static or animated wallpaper.':'两种桌面都能搭配下面 10 套静态或动态壁纸。'}</p></div></div>
    <div className={cs.modeGrid} role="group" aria-label={en?'Desktop style':'桌面风格'}>{(['windows','mac'] as const).map(mode=><button key={mode} className={cs.modeCard} aria-pressed={selected===mode} disabled={busy} onClick={()=>{touched.current=true;setSelected(mode);setMessage('');}}>
      <div className={`${cs.miniDesktop} ${mode==='mac'?cs.macDesktop:''}`} aria-hidden="true">{mode==='mac'&&<div className={cs.miniToolbar}><span>●　Finder　文件　编辑</span><span>◉　◔</span></div>}<div className={cs.miniWindow}><i/><i/><i/><div/><div/></div><div className={cs.miniTaskbar}>{['#6b9bdf','#86b6a7','#c19ed1','#ddb580','#7f97c9'].map(color=><i style={{background:color}}/>)}</div></div>
      <div className={cs.modeLabel}><strong>{mode==='mac'?(en?'Mac style':'Mac 风格'):'Windows'}</strong><span>{state?.desktopMode===mode?(en?'Active':'当前模式'):selected===mode?(en?'Selected':'已选择'):''}</span></div>
      <p>{mode==='mac'?(en?'Floating Dock + top toolbar':'底部悬浮 Dock + 顶部工具栏'):(en?'Original Windows taskbar and Start menu':'Windows 原生任务栏与开始菜单')}</p>
    </button>)}</div>
    <div className={cs.modeFooter}><span>{en?'Mac style runs on Windows using Seelen.': 'Mac 风格由 Seelen 提供，仍使用 Windows 系统。'}{!native&&(en?' Open the desktop app to apply.':' 请在桌面应用中切换。')}{native&&state?.desktopMode==='custom'&&(en?' Current layout is customized.':' 当前为自定义布局。')}</span><button className={cs.apply} disabled={!native||!state||busy||(selected==='mac'&&!state.seelen.available)} onClick={()=>void apply()}>{busy?(en?'Switching…':'正在切换…'):(en?`Apply ${selected==='mac'?'Mac style':'Windows'}`:`切换为 ${selected==='mac'?'Mac 风格':'Windows'}`)}</button></div>
    {message&&<p role="status" className={cs.success}>{message}</p>}{error&&<p role="alert" className={cs.error}>{error}</p>}
  </section>;
}
