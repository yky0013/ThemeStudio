// SPDX-License-Identifier: AGPL-3.0-or-later
import { useEffect, useRef, useState } from 'preact/hooks';
import { useTranslation } from 'react-i18next';
import type { DesktopClient } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts';
import type { RuntimeState } from './runtime.tsx';
import cs from './templates.module.css';
import { appearanceDraft } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/appearance.ts';

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
      if(alive){setState(next);appearanceDraft.desktopMode=next.desktopMode;if(!touched.current)setSelected(next.desktopMode==='mac'?'mac':'windows');}
    }).catch(failure=>{if(alive)setError(String(failure));});};
    const changed=(event:Event)=>{const next=(event as CustomEvent<RuntimeState>).detail;if(next){setState(next);appearanceDraft.desktopMode=next.desktopMode;if(!touched.current)setSelected(next.desktopMode==='mac'?'mac':'windows');}else refresh();};
    const reset=()=>{touched.current=false;refresh();};
    document.addEventListener('theme-studio-appearance-complete',reset);document.addEventListener('theme-studio-draft-discarded',reset);
    refresh();document.addEventListener('theme-studio-runtime-state',changed);
    return()=>{alive=false;document.removeEventListener('theme-studio-runtime-state',changed);document.removeEventListener('theme-studio-appearance-complete',reset);document.removeEventListener('theme-studio-draft-discarded',reset);};
  },[client,native]);
  return <section id="workbench-desktop-mode" className={`${cs.library} ${cs.modeSection}`}>
    <div className={cs.heading}><div><p className={cs.eyebrow}>YOUR DESKTOP, YOUR WAY</p><h2>{en?'Choose your desktop style':'先选一种桌面风格'}</h2><p>{en?'Pair either layout with any static or animated wallpaper.':'两种桌面都能搭配内置静态套装，或导入自己的动态壁纸。'}</p></div></div>
    <div className={cs.modeGrid} role="group" aria-label={en?'Desktop style':'桌面风格'}>{(['windows','mac'] as const).map(mode=><button key={mode} className={cs.modeCard} aria-pressed={selected===mode} disabled={busy} onClick={()=>{touched.current=true;setSelected(mode);setMessage(en?'Selected; apply with the shared button below.':'已加入待应用，通过底部统一应用。');appearanceDraft.set('desktop',{label:mode==='mac'?'Mac 桌面':'Windows 桌面',operation:'runtime.desktop.apply',payload:{mode}});}}>
      <div className={`${cs.miniDesktop} ${mode==='mac'?cs.macDesktop:''}`} aria-hidden="true">{mode==='mac'&&<div className={cs.miniToolbar}><span>●　Finder　文件　编辑</span><span>◉　◔</span></div>}<div className={cs.miniWindow}><i/><i/><i/><div/><div/></div><div className={cs.miniTaskbar}>{['#6b9bdf','#86b6a7','#c19ed1','#ddb580','#7f97c9'].map(color=><i style={{background:color}}/>)}</div></div>
      <div className={cs.modeLabel}><strong>{mode==='mac'?(en?'Mac style':'Mac 风格'):'Windows'}</strong><span>{state?.desktopMode===mode?(en?'Active':'当前模式'):selected===mode?(en?'Selected':'已选择'):''}</span></div>
      <p>{mode==='mac'?(en?'Floating Dock + top toolbar':'底部悬浮 Dock + 顶部工具栏'):(en?'Original Windows taskbar and Start menu':'Windows 原生任务栏与开始菜单')}</p>
    </button>)}</div>
    <div className={cs.modeFooter}><span>{en?'Mac style runs on Windows using Seelen.': 'Mac 风格由 Seelen 提供，仍使用 Windows 系统。'}{!native&&(en?' Open the desktop app to apply.':' 请在桌面应用中切换。')}{native&&state?.desktopMode==='custom'&&(en?' Current layout is customized.':' 当前为自定义布局。')}</span></div>
    {message&&<p role="status" className={cs.success}>{message}</p>}{error&&<p role="alert" className={cs.error}>{error}</p>}
  </section>;
}
