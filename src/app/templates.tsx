// SPDX-License-Identifier: AGPL-3.0-or-later
import { useEffect, useRef, useState } from 'preact/hooks';
import type { DesktopClient } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts';
import { bundledPack, packAsset, packMode, type ThemePack } from './theme-pack.ts';
import cs from './templates.module.css';
import { appearanceDraft } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/appearance.ts';
import { ExplorerPreview, defaultExplorerAppearance } from './explorer-preview.tsx';

interface Applied { name: string; iconsApplied: number; cursorsApplied: number; mode: 'static' | 'animated'; explorerApplied?: boolean }
export function TemplateLibrary({client,native}:{client:DesktopClient;native:boolean}) {
  const [packs,setPacks]=useState<ThemePack[]>([]);
  const [selected,setSelected]=useState<ThemePack|null>(null);
  const [candidate,setCandidate]=useState<ThemePack|null>(null);
  const [active,setActive]=useState(localStorage.getItem('theme-studio.template')||'');
  const [icons,setIcons]=useState(false);
  const [cursors,setCursors]=useState(false);
  const [wallpaperMode,setWallpaperMode]=useState<'static'|'animated'>('static');
  const [previewTab,setPreviewTab]=useState<'wallpaper'|'explorer'>('wallpaper');
  const [explorerOpacity,setExplorerOpacity]=useState(defaultExplorerAppearance.imageOpacity);
  const [explorer,setExplorer]=useState(true);
  const [explorerSupported,setExplorerSupported]=useState<boolean|null>(null);
  const [busy,setBusy]=useState('');
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  const running=useRef(false);
  const alive=useRef(true);
  const load=async()=>{
    const items=native?(await client.call<{packs:ThemePack[]}>('templates.list')).packs:
      await fetch('/templates/catalog.json').then(response=>{if(!response.ok)throw new Error('模板资源不完整，请重新安装。');return response.json();}).then(items=>items.map(bundledPack));
    if(native){
      const support=await client.call<{supported:boolean}>('explorer.state');
      if(alive.current){setExplorerSupported(support.supported);if(!support.supported)setExplorer(false);}
    }
    if(alive.current)setPacks(items);
    return items as ThemePack[];
  };
  useEffect(()=>{
    alive.current=true;
    void load().catch(failure=>{if(alive.current)setError(String(failure));});
    return()=>{alive.current=false;};
  },[client,native]);
  useEffect(()=>{
    if(!selected)return;
    const key=(event:KeyboardEvent)=>{if(event.key==='Escape'&&!running.current)setSelected(null);};
    document.addEventListener('keydown',key);return()=>document.removeEventListener('keydown',key);
  },[selected]);
  const run=async(key:string,action:()=>Promise<void>)=>{
    if(running.current)return;
    running.current=true;setBusy(key);setError('');setMessage('');
    try{await action();}catch(failure){setError(failure instanceof Error?failure.message:String(failure));}
    finally{running.current=false;setBusy('');}
  };
  const importPack=()=>run('import',async()=>{
    const result=await client.call<{id:string;name:string;version:string;duplicate:boolean;updated?:boolean}|null>('templates.import');
    if(!result)return;
    if(result.updated&&active===result.id){setActive('');localStorage.removeItem('theme-studio.template');}
    const items=await load();
    document.dispatchEvent(new CustomEvent('theme-studio-packs-changed'));
    setSelected(items.find(item=>item.id===result.id)||null);
    setMessage(result.duplicate?`${result.name} v${result.version} 已在套装库中。`:`已${result.updated?'更新':'导入'} ${result.name} v${result.version}。可以先预览、选择，再从底部统一应用。`);
  });
  const exportPack=(pack:ThemePack)=>run('export',async()=>{
    const result=await client.call<{path:string}|null>('templates.export',{id:pack.id});
    if(result)setMessage(`完整套装已导出：${result.path}`);
  });
  const choose=(pack:ThemePack)=>{setCandidate(pack);setSelected(null);setMessage(`已选择 ${pack.name}，请使用底部“应用当前主题”。`);};
  useEffect(()=>{
    if(candidate)appearanceDraft.set('theme',{label:candidate.name,operation:'templates.apply',accent:candidate.accent,payload:{id:candidate.id,icons,cursors,wallpaperMode:packMode(candidate,wallpaperMode),explorer:explorer&&explorerSupported!==false,explorerAppearance:{...defaultExplorerAppearance,imageOpacity:explorerOpacity}}});
  },[candidate,icons,cursors,wallpaperMode,explorer,explorerSupported,explorerOpacity]);
  useEffect(()=>{
    const clear=()=>{setCandidate(null);setMessage('');setActive(localStorage.getItem('theme-studio.template')||'');};
    document.addEventListener('theme-studio-appearance-complete',clear);document.addEventListener('theme-studio-draft-discarded',clear);
    return()=>{document.removeEventListener('theme-studio-appearance-complete',clear);document.removeEventListener('theme-studio-draft-discarded',clear);};
  },[]);
  const previewMode=selected?packMode(selected,wallpaperMode):wallpaperMode;
  return <section id="workbench-templates" className={cs.library}>
    <div className={cs.heading}><div><p className={cs.eyebrow}>YOUR THEME COLLECTIONS · {packs.length} 套</p><h2>选择一套喜欢的主题，再统一应用</h2><p>内置主题随时用，也可导入数据包，添加自己的壁纸、指针与图标套装。</p></div><div className={cs.toolbar}><button disabled={!native||!!busy} onClick={()=>{document.getElementById("workbench-parallax")?.scrollIntoView({behavior:"smooth"});document.dispatchEvent(new CustomEvent("theme-studio-import-wallpaper"));}}>导入图片 / 动图 / 视频</button><button className={cs.apply} disabled={!native||!!busy} onClick={()=>void importPack()}>{busy==='import'?'正在导入…':'导入主题数据包'}</button></div></div>
    <div className={cs.options}>{packs.some(pack=>pack.animatedWallpaper)&&<div className={cs.segmented} role="group" aria-label="模板壁纸模式">{(['static','animated'] as const).map(mode=><button key={mode} aria-pressed={wallpaperMode===mode} disabled={!!busy} onClick={()=>{setWallpaperMode(mode);localStorage.setItem('theme-studio.wallpaper-mode',mode);setError('');}}>{mode==='animated'?'▶ 动态壁纸':'▧ 静态壁纸'}</button>)}</div>}<label><input type="checkbox" checked={cursors} disabled={!!busy} onChange={e=>setCursors(e.currentTarget.checked)}/>鼠标指针</label><label><input type="checkbox" checked={icons} disabled={!!busy} onChange={e=>setIcons(e.currentTarget.checked)}/>匹配的桌面图标</label><span className={cs.hint}>{wallpaperMode==='animated'?'仅使用已导入套装中的动态版；其余使用静态壁纸':'动态素材可直接导入 · 静态无需后台播放'}</span></div>
    {message&&<p role="status" className={cs.success}>{message}</p>}{error&&<p role="alert" className={cs.error}>{error}</p>}
    <div className={cs.grid}>{packs.map(pack=><article key={pack.id} className={cs.card} style={{'--pack-accent':pack.accent}}>
      <button className={cs.art} aria-label={`预览${pack.name}`} disabled={!!busy} onClick={()=>{setError('');setSelected(pack);}}><img src={packAsset(pack,pack.thumbnail)} alt={pack.subtitle||pack.name} loading="lazy" decoding="async" width="640" height="360"/>{active===pack.id&&<span className={cs.badge}>已应用</span>}<span className={cs.motionBadge}>{pack.source==='imported'?'已导入 · ':''}{pack.animatedWallpaper?'▶ 含动态版':'静态套装'}</span></button>
      <div className={cs.cardBody}><div><h3>{pack.name}</h3><p>{pack.subtitle}</p><p className={cs.packMeta}>{pack.source==='imported'?`已导入 · v${pack.version}`:'内置'} · {Object.keys(pack.icons).length} 款图标 · {Object.keys(pack.cursors).length} 状态指针</p></div><div className={cs.swatches}><i style={{background:pack.accent}}/><i style={{background:pack.pale}}/><i style={{background:'#faf8ff'}}/></div></div>
      <div className={cs.actions}><button disabled={!!busy} onClick={()=>setSelected(pack)}>查看预览</button><button className={cs.apply} disabled={!!busy} aria-pressed={candidate?.id===pack.id} onClick={()=>choose(pack)}>{candidate?.id===pack.id?'已选择':'选择此主题'}</button></div>
    </article>)}</div>
    <label className={cs.explorerChoice}><input type="checkbox" checked={explorer} disabled={!!busy||explorerSupported===false} onChange={e=>setExplorer(e.currentTarget.checked)}/> 同时应用主题到文件资源管理器{explorerSupported===false?'（需要 Windows 11 22H2）':''}</label>
    <p className={cs.footnote}>安装、打开和预览保留当前桌面。点击应用时联动壁纸与资源管理器；鼠标指针和桌面图标按勾选应用。资源管理器使用静态背景。支持 .tspack / .zip 导入与完整导出，应用前自动备份。</p>
    {selected&&<div className={cs.scrim} onClick={e=>{if(e.target===e.currentTarget&&!busy)setSelected(null);}}><div className={cs.dialog} role="dialog" aria-modal="true" aria-label={`${selected.name}模板预览`}>
      <div className={cs.dialogHeading}><div><h2>{selected.name}</h2><p>{selected.subtitle}{selected.author?` · ${selected.author}`:''} · v{selected.version}</p></div><button aria-label="关闭预览" disabled={!!busy} onClick={()=>setSelected(null)}>✕</button></div>
      <div className={cs.previewModes} role="group" aria-label="预览区域"><button aria-pressed={previewTab==='wallpaper'} onClick={()=>setPreviewTab('wallpaper')}>桌面壁纸</button><button aria-pressed={previewTab==='explorer'} onClick={()=>setPreviewTab('explorer')}>文件资源管理器</button><span>仅预览，点击应用后才改变系统</span></div>
      {previewTab==='wallpaper'&&selected.animatedWallpaper&&<div className={cs.previewModes} role="group" aria-label="预览壁纸模式">{(['static','animated'] as const).map(mode=><button key={mode} aria-pressed={previewMode===mode} disabled={!!busy||(mode==='animated'&&!selected.animatedWallpaper)} onClick={()=>{setWallpaperMode(mode);localStorage.setItem('theme-studio.wallpaper-mode',mode);setError('');}}>{mode==='animated'?'播放动态版':'查看静态版'}</button>)}<span>{previewMode==='animated'?selected.motionLabel:'静态壁纸'}</span></div>}
      {previewTab==='explorer'?<div className={cs.explorerInset}><label>背景图片可见度　<input aria-label="主题资源管理器背景可见度" type="range" min="10" max="70" value={explorerOpacity} disabled={!!busy} onInput={e=>setExplorerOpacity(Number(e.currentTarget.value))}/> {explorerOpacity}%</label><ExplorerPreview image={packAsset(selected,selected.wallpaper)} name={selected.name} appearance={{...defaultExplorerAppearance,imageOpacity:explorerOpacity}}/></div>:previewMode==='animated'?<video key={selected.id} className={cs.wallpaper} src={packAsset(selected,selected.animatedWallpaper!)} poster={packAsset(selected,selected.wallpaper)} aria-label={`${selected.name}动态壁纸预览`} controls autoPlay={!matchMedia('(prefers-reduced-motion: reduce)').matches} loop muted playsInline preload="metadata" onError={()=>setError('动态壁纸加载失败，请检查数据包中的视频编码是否受支持。')}/>:<img className={cs.wallpaper} src={packAsset(selected,selected.wallpaper)} alt={selected.subtitle||selected.name} onError={()=>setError('预览图片加载失败，请重新导入数据包或检查程序目录。')}/>}
      <label className={cs.explorerInset}><input type="checkbox" checked={explorer} disabled={!!busy||explorerSupported===false} onChange={e=>setExplorer(e.currentTarget.checked)}/> 应用时同步资源管理器背景{explorerSupported===false?'（需要 Windows 11 22H2）':''}</label>
      {error&&<p role="alert" className={cs.error}>{error}</p>}{message&&<p role="status" className={cs.success}>{message}</p>}
      {previewTab==='wallpaper'&&<div className={cs.previewAccessories}><span>{Object.keys(selected.icons).length?'配套图标':'不含配套图标'}</span>{Object.entries(selected.icons).slice(0,6).map(([symbol,icon])=><img key={symbol} src={packAsset(selected,icon.file)} width="38" height="38" alt={symbol}/>)}<span>{Object.keys(selected.cursors).length?`${Object.keys(selected.cursors).length} 状态指针`:'不含配套指针'}</span>{selected.cursorPreview&&<img src={packAsset(selected,selected.cursorPreview)} width="44" height="44" alt="鼠标指针预览"/>}</div>}
      {previewTab==='wallpaper'&&selected.source==='builtin'&&<details className={cs.allAccessories} open><summary>查看全部角色图标与 17 种指针状态</summary><img src={packAsset(selected,`${selected.id}/accessories-preview.png`)} alt={`${selected.name}全部图标与鼠标指针，点击位置位于左上方功能符号`} loading="lazy"/></details>}
      <div className={cs.dialogFooter}><span>{previewMode==='animated'?'动态循环播放':'静态省内存'} · 应用前自动备份</span><div className={cs.toolbar}><button disabled={!native||!!busy} onClick={()=>void exportPack(selected)}>{busy==='export'?'正在导出…':'导出完整套装'}</button><button className={cs.apply} disabled={!!busy} onClick={()=>choose(selected)}>选择并关闭预览</button></div></div>
    </div></div>}
  </section>;
}
