// SPDX-License-Identifier: AGPL-3.0-or-later
import { useEffect, useRef, useState } from 'preact/hooks';
import type { DesktopClient } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts';
import cs from './templates.module.css';
import sourceData from './pet-sources.json';
const sources: {name:string;kind:string;url:string;note:string}[] = sourceData;

interface Pet { id:string; name:string; path:string; available:boolean; running:boolean }
export function PetPanel({client,native}:{client:DesktopClient;native:boolean}) {
  const [pets,setPets]=useState<Pet[]>([]);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  const running=useRef(false);
  const refresh=async()=>setPets((await client.call<{pets:Pet[]}>('pets.state')).pets);
  useEffect(()=>{if(native)void refresh().catch(e=>setError(String(e)));},[native,client]);
  const run=async(action:'import'|'launch'|'remove'|'refresh',id?:string)=>{
    if(running.current)return;running.current=true;setBusy(true);setError('');setMessage('');
    try {
      if(action==='import'){
        const result=await client.call<{name:string}|null>('pets.import');
        if(result)setMessage(`已导入 ${result.name}，点击“启动桌宠”即可打开。`);
      } else if(action==='launch'){
        const result=await client.call<{alreadyRunning:boolean}>('pets.launch',{id});
        setMessage(result.alreadyRunning?'该主程序已经在运行。':'已发送启动请求。若桌宠另开子进程，运行状态可能无法识别；请以桌面显示为准。');
      } else if(action==='remove'){
        await client.call('pets.remove',{id});setMessage('已从列表移除，桌宠原文件保留。');
      }
      await refresh();
    }catch(e){setError(e instanceof Error?e.message:String(e));}
    finally{running.current=false;setBusy(false);}
  };
  return <section id="workbench-pets" className={cs.library}>
    <div className={cs.heading}><div><p className={cs.eyebrow}>DESKTOP COMPANIONS</p><h2>让喜欢的角色住在桌面上</h2><p>下载并安装或解压桌宠，选择它的 EXE 主程序，直接加入桌宠库。</p></div><div className={cs.toolbar}><button className={cs.apply} disabled={!native||busy} onClick={()=>void run('import')}>导入桌宠 EXE</button><button disabled={!native||busy} onClick={()=>void run('refresh')}>刷新状态</button></div></div>
    {pets.length===0&&<p className={cs.hint}>还没有导入桌宠。下方来源可先查看，再选择喜欢的桌宠下载。</p>}
    <div className={cs.grid}>{pets.map(pet=><article className={cs.card} key={pet.id}><div className={cs.cardBody}><div><h3>{pet.name}</h3><p>{!pet.available?'原文件已移动，请重新导入':pet.running?'主程序运行中':'已导入'}</p><p className={cs.petPath} title={pet.path}>{pet.path}</p></div></div><div className={cs.actions}><button disabled={busy} onClick={()=>void run('remove',pet.id)}>移除记录</button><button className={cs.apply} disabled={busy||!pet.available} onClick={()=>void run('launch',pet.id)}>启动桌宠</button></div></article>)}</div>
    {message&&<p className={cs.success} role="status">{message}</p>}{error&&<p className={cs.error} role="alert">{error}</p>}
    <h3>桌宠来源</h3><div className={cs.grid}>{sources.map(source=><article className={cs.card} key={source.name}><div className={cs.cardBody}><div><p className={cs.packMeta}>{source.kind}</p><h3>{source.name}</h3><p>{source.note}</p></div></div><div className={cs.actions}><a href={source.url} target="_blank" rel="noopener noreferrer">查看原发布页 ↗</a></div></article>)}</div>
    <p className={cs.footnote}>导入只登记路径，不移动桌宠文件夹，也不会自动启动。请选主程序而非安装器；模型包、Steam 创意工坊订阅和 Shimeji 素材需先在对应引擎中导入，再登记引擎 EXE。互动、关闭和开机启动由桌宠自身控制。这里只提供来源入口，不内置第三方角色素材。</p>
  </section>;
}
