// SPDX-License-Identifier: AGPL-3.0-or-later
import { useEffect, useRef, useState } from 'preact/hooks';
import type { DesktopClient } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts';
import { bundledPack, packAsset, packMode, type ThemePack } from './theme-pack.ts';
import cs from './templates.module.css';

interface Applied { name: string; iconsApplied: number; cursorsApplied: number; mode: 'static' | 'animated' }
export function TemplateLibrary({client,native}:{client:DesktopClient;native:boolean}) {
  const [packs,setPacks]=useState<ThemePack[]>([]);
  const [selected,setSelected]=useState<ThemePack|null>(null);
  const [active,setActive]=useState(localStorage.getItem('theme-studio.template')||'');
  const [icons,setIcons]=useState(true);
  const [cursors,setCursors]=useState(true);
  const [wallpaperMode,setWallpaperMode]=useState<'static'|'animated'>(localStorage.getItem('theme-studio.wallpaper-mode')==='static'?'static':'animated');
  const [busy,setBusy]=useState('');
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  const running=useRef(false);
  const alive=useRef(true);
  const load=async()=>{
    const items=native?(await client.call<{packs:ThemePack[]}>('templates.list')).packs:
      await fetch('/templates/catalog.json').then(response=>{if(!response.ok)throw new Error('模板资源不完整，请重新安装。');return response.json();}).then(items=>items.map(bundledPack));
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
    setSelected(items.find(item=>item.id===result.id)||null);
    setMessage(result.duplicate?`${result.name} v${result.version} 已在套装库中。`:`已${result.updated?'更新':'导入'} ${result.name} v${result.version}。可以先预览，再一键应用。`);
  });
  const exportPack=(pack:ThemePack)=>run('export',async()=>{
    const result=await client.call<{path:string}|null>('templates.export',{id:pack.id});
    if(result)setMessage(`完整套装已导出：${result.path}`);
  });
  const apply=(pack:ThemePack)=>run(pack.id,async()=>{
    const mode=packMode(pack,wallpaperMode);
    const result=await client.call<Applied>('templates.apply',{id:pack.id,icons,cursors,wallpaperMode:mode});
    localStorage.setItem('theme-studio.wallpaper-mode',mode);
    localStorage.setItem('theme-studio.template',pack.id);localStorage.setItem('theme-studio.accent',pack.accent);setActive(pack.id);
    document.dispatchEvent(new CustomEvent('theme-studio-template-applied',{detail:{accent:pack.accent}}));
    document.dispatchEvent(new CustomEvent('theme-studio-wallpaper-changed'));
    setMessage(`${result.name}已应用：${result.mode==='animated'?'动态':'静态'}壁纸${result.cursorsApplied?'、17 种鼠标状态':''}${result.iconsApplied?`、${result.iconsApplied} 个桌面快捷方式`:''}。${result.mode==='animated'?'可在壁纸与视差区域暂停或停止。':'静态壁纸无需后台播放。'}`);
    setSelected(null);
  });
  const restore=()=>run('restore',async()=>{
    await client.call('templates.restore');setActive('');localStorage.removeItem('theme-studio.template');localStorage.removeItem('theme-studio.accent');
    document.dispatchEvent(new CustomEvent('theme-studio-template-applied',{detail:{accent:'#7967c6'}}));setMessage('已恢复上一次模板应用前的壁纸、指针和快捷方式。');
    document.dispatchEvent(new CustomEvent('theme-studio-wallpaper-changed'));
  });
  const previewMode=selected?packMode(selected,wallpaperMode):wallpaperMode;
  return <section id="workbench-templates" className={cs.library}>
    <div className={cs.heading}><div><p className={cs.eyebrow}>YOUR THEME COLLECTIONS · {packs.length} 套</p><h2>选一套喜欢的，桌面即刻焕新</h2><p>内置主题随时用，也可导入数据包，添加自己的壁纸、指针与图标套装。</p></div><div className={cs.toolbar}><button className={cs.apply} disabled={!native||!!busy} onClick={()=>void importPack()}>{busy==='import'?'正在导入…':'导入主题数据包'}</button><button disabled={!native||!!busy} onClick={()=>void restore()}>{busy==='restore'?'正在恢复…':'恢复上一次应用'}</button></div></div>
    <div className={cs.options}><div className={cs.segmented} role="group" aria-label="模板壁纸模式">{(['static','animated'] as const).map(mode=><button key={mode} aria-pressed={wallpaperMode===mode} disabled={!!busy} onClick={()=>{setWallpaperMode(mode);localStorage.setItem('theme-studio.wallpaper-mode',mode);setError('');}}>{mode==='animated'?'▶ 动态壁纸':'▧ 静态壁纸'}</button>)}</div><label><input type="checkbox" checked={cursors} disabled={!!busy} onChange={e=>setCursors(e.currentTarget.checked)}/>鼠标指针</label><label><input type="checkbox" checked={icons} disabled={!!busy} onChange={e=>setIcons(e.currentTarget.checked)}/>匹配的桌面图标</label><span className={cs.hint}>{wallpaperMode==='animated'?'没有动态版的套装使用静态壁纸':'静态省内存 · 无需后台播放'}</span></div>
    {message&&<p role="status" className={cs.success}>{message}</p>}{error&&<p role="alert" className={cs.error}>{error}</p>}
    <div className={cs.grid}>{packs.map(pack=><article key={pack.id} className={cs.card} style={{'--pack-accent':pack.accent}}>
      <button className={cs.art} aria-label={`预览${pack.name}`} disabled={!!busy} onClick={()=>{setError('');setSelected(pack);}}><img src={packAsset(pack,pack.thumbnail)} alt={pack.subtitle||pack.name} loading="lazy" decoding="async" width="640" height="360"/>{active===pack.id&&<span className={cs.badge}>已应用</span>}<span className={cs.motionBadge}>{pack.source==='imported'?'已导入 · ':''}{pack.animatedWallpaper?'▶ 含动态版':'静态套装'}</span></button>
      <div className={cs.cardBody}><div><h3>{pack.name}</h3><p>{pack.subtitle}</p><p className={cs.packMeta}>{pack.source==='imported'?`已导入 · v${pack.version}`:'内置'} · {Object.keys(pack.icons).length} 款图标 · {Object.keys(pack.cursors).length} 状态指针</p></div><div className={cs.swatches}><i style={{background:pack.accent}}/><i style={{background:pack.pale}}/><i style={{background:'#faf8ff'}}/></div></div>
      <div className={cs.actions}><button disabled={!!busy} onClick={()=>setSelected(pack)}>查看预览</button><button className={cs.apply} disabled={!native||!!busy} onClick={()=>void apply(pack)}>{busy===pack.id?'正在应用…':'一键应用'}</button></div>
    </article>)}</div>
    <p className={cs.footnote}>支持 .tspack / .zip 完整主题数据包。导入后保存在本机，重启和升级后仍可使用；预览中可导出完整套装。应用前自动备份。内置动态版为 AI 同人插画的缓慢运镜与柔光动效。</p>
    {selected&&<div className={cs.scrim} onClick={e=>{if(e.target===e.currentTarget&&!busy)setSelected(null);}}><div className={cs.dialog} role="dialog" aria-modal="true" aria-label={`${selected.name}模板预览`}>
      <div className={cs.dialogHeading}><div><h2>{selected.name}</h2><p>{selected.subtitle}{selected.author?` · ${selected.author}`:''} · v{selected.version}</p></div><button aria-label="关闭预览" disabled={!!busy} onClick={()=>setSelected(null)}>✕</button></div>
      <div className={cs.previewModes} role="group" aria-label="预览壁纸模式">{(['static','animated'] as const).map(mode=><button key={mode} aria-pressed={previewMode===mode} disabled={!!busy||(mode==='animated'&&!selected.animatedWallpaper)} onClick={()=>{setWallpaperMode(mode);localStorage.setItem('theme-studio.wallpaper-mode',mode);setError('');}}>{mode==='animated'?'播放动态版':'查看静态版'}</button>)}<span>{previewMode==='animated'?selected.motionLabel:'静态壁纸'}</span></div>
      {previewMode==='animated'?<video key={selected.id} className={cs.wallpaper} src={packAsset(selected,selected.animatedWallpaper!)} poster={packAsset(selected,selected.wallpaper)} aria-label={`${selected.name}动态壁纸预览`} controls autoPlay={!matchMedia('(prefers-reduced-motion: reduce)').matches} loop muted playsInline preload="metadata" onError={()=>setError('动态壁纸加载失败，请检查数据包中的视频编码是否受支持。')}/>:<img className={cs.wallpaper} src={packAsset(selected,selected.wallpaper)} alt={selected.subtitle||selected.name} onError={()=>setError('预览图片加载失败，请重新导入数据包或检查程序目录。')}/>}
      {error&&<p role="alert" className={cs.error}>{error}</p>}{message&&<p role="status" className={cs.success}>{message}</p>}
      <div className={cs.previewAccessories}><span>{Object.keys(selected.icons).length?'配套图标':'不含配套图标'}</span>{Object.entries(selected.icons).slice(0,6).map(([symbol,icon])=><img key={symbol} src={packAsset(selected,icon.file)} width="38" height="38" alt={symbol}/>)}<span>{Object.keys(selected.cursors).length?'17 状态指针':'不含配套指针'}</span>{selected.cursorPreview&&<img src={packAsset(selected,selected.cursorPreview)} width="44" height="44" alt="鼠标指针预览"/>}</div>
      <div className={cs.dialogFooter}><span>{previewMode==='animated'?'动态循环播放':'静态省内存'} · 应用前自动备份</span><div className={cs.toolbar}><button disabled={!native||!!busy} onClick={()=>void exportPack(selected)}>{busy==='export'?'正在导出…':'导出完整套装'}</button><button className={cs.apply} disabled={!native||!!busy} onClick={()=>void apply(selected)}>{busy===selected.id?'正在应用…':`应用${previewMode==='animated'?'动态':'静态'}版套装`}</button></div></div>
    </div></div>}
  </section>;
}
