// SPDX-License-Identifier: AGPL-3.0-or-later
import { useEffect, useRef, useState } from 'preact/hooks';
import type { DesktopClient } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts';
import { bundledPack, packAsset, type ThemePack } from './theme-pack.ts';
import { ExplorerPreview, defaultExplorerAppearance, type ExplorerAppearance } from './explorer-preview.tsx';
import cs from './templates.module.css';
import { appearanceDraft } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/appearance.ts';

interface ExplorerState {
  supported:boolean; build:number; available:boolean; canRestore:boolean;
  image:{active:boolean; packId:string; appearance:ExplorerAppearance; enabled:boolean; loaded:boolean};
}
export function ExplorerPanel({client,native}:{client:DesktopClient;native:boolean}) {
  const [state,setState]=useState<ExplorerState|null>(null);
  const [packs,setPacks]=useState<ThemePack[]>([]);
  const [packId,setPackId]=useState('');
  const [look,setLook]=useState<ExplorerAppearance>(defaultExplorerAppearance);
  const [busy,setBusy]=useState(false);
  const [dirty,setDirty]=useState(false);
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  const running=useRef(false);
  const touched=useRef(false);
  const refresh=async()=>{
    const items:ThemePack[]=native?(await client.call<{packs:ThemePack[]}>('templates.list')).packs:
      await fetch('/templates/catalog.json').then(r=>r.json()).then(items=>items.map(bundledPack));
    setPacks(items);
    const next=native?await client.call<ExplorerState>('explorer.state'):null;
    setState(next);
    if(!touched.current){
      const selected=next?.image.packId||localStorage.getItem('theme-studio.template');
      setPackId(items.find(p=>p.id===selected)?.id||items[0]?.id||'');
      setLook(next?.image.appearance||defaultExplorerAppearance);
    }
    return next;
  };
  useEffect(()=>{
    const update=()=>{touched.current=false;setDirty(false);void refresh().catch(e=>setError(String(e)));};
    update();document.addEventListener('theme-studio-template-applied',update);
    document.addEventListener('theme-studio-packs-changed',update);
    return()=>{document.removeEventListener('theme-studio-template-applied',update);document.removeEventListener('theme-studio-packs-changed',update);};
  },[native,client]);
  useEffect(()=>{
    if(dirty&&packId)appearanceDraft.set('explorer',{label:'资源管理器背景',operation:'explorer.apply',payload:{mode:'image',packId,appearance:look},error:state&&!state.supported?'此系统不支持资源管理器图片外观':undefined});
  },[dirty,packId,look,state?.supported]);
  useEffect(()=>{const clear=()=>{setDirty(false);touched.current=false;void refresh().catch(e=>setError(String(e)));};document.addEventListener('theme-studio-draft-discarded',clear);return()=>document.removeEventListener('theme-studio-draft-discarded',clear);},[]);
  const pack=packs.find(p=>p.id===packId);
  return <section id="workbench-explorer" className={cs.library}>
    <div className={cs.heading}><div><p className={cs.eyebrow}>FILE EXPLORER</p><h2>让主题延伸到资源管理器</h2><p>主题图片进入文件列表，搭配深色面板与清晰文字。可在这里调整，随后通过底部入口与其他设置一起应用。</p></div></div>
    <div className={cs.options}>
      <label>背景主题 <select aria-label="资源管理器背景主题" value={packId} disabled={busy} onChange={e=>{touched.current=true;setDirty(true);setPackId(e.currentTarget.value);}}>{packs.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
      <label>图片可见度 <input aria-label="资源管理器图片可见度" type="range" min="10" max="70" value={look.imageOpacity} disabled={busy} onInput={e=>{touched.current=true;setDirty(true);setLook({...look,imageOpacity:Number(e.currentTarget.value)});}}/> {look.imageOpacity}%</label>
      <span className={cs.hint}>调整后实时预览 · 点击应用才改变系统</span>
    </div>
    <ExplorerPreview image={pack&&packAsset(pack,pack.wallpaper)} name={pack?.name||'选择主题'} appearance={look}/>
    <div className={cs.toolbar}><span>这里的调整只加入待应用；通过底部按钮统一应用或恢复。</span><button disabled={busy||!native} onClick={()=>void refresh().catch(e=>setError(String(e)))}>刷新状态</button></div>
    <p className={cs.hint}>{state?`Windows build ${state.build} · ${!state.supported?'需要 Windows 11 22H2 或更新版本':!state.available?'运行组件不完整':state.image.active?`${state.image.enabled?'已启用':'配置已保存，组件未启用'} · ${state.image.loaded?'已检测到图片组件载入':'尚未检测到图片组件载入'}`:'尚未应用图片背景'}`:'可预览效果；应用请使用桌面安装版。'}</p>
    <p className={cs.footnote}>使用主题静态图片，动态主题取静态封面。首次应用需编译原生组件。文件列表、主文件夹与工具栏由不同 Windows 控件绘制，具体布局随系统版本变化。</p>
    {message&&<p className={cs.success} role="status">{message}</p>}{error&&<p className={cs.error} role="alert">{error}</p>}
  </section>;
}
