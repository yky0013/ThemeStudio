// SPDX-License-Identifier: AGPL-3.0-or-later
import { useEffect,useRef,useState } from 'preact/hooks';
import type { DesktopClient } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts';
import { appearanceDraft } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/appearance.ts';
import cs from './appearance.module.css';

interface RecoveryState { canUndo:boolean; canRestoreInitial:boolean; pending:boolean; lastLabel?:string; baselineLabel?:string; }
export function AppearanceBar({client,native}:{client:DesktopClient;native:boolean}){
  const [,revision]=useState(0);
  const [state,setState]=useState<RecoveryState|null>(null);
  const [message,setMessage]=useState('');const [error,setError]=useState('');
  const running=useRef(false);
  const refresh=async()=>setState(await client.call<RecoveryState>('appearance.state'));
  useEffect(()=>appearanceDraft.subscribe(()=>revision(n=>n+1)),[]);
  useEffect(()=>{if(native)void refresh().catch(e=>setError(String(e)));},[client,native]);
  const run=async(kind:'apply'|'last'|'initial')=>{
    if(running.current)return;running.current=true;appearanceDraft.setBusy(true);setMessage('');setError('');
    const operations=appearanceDraft.plan();
    try{
      const result=await client.call<{message?:string}>('appearance.'+(kind==='apply'?'apply':'restore'),
        kind==='apply'?{operations:operations.map(({operation,payload,label})=>({operation,payload,label}))}:{kind});
      if(kind==='apply'){
        const selected=operations.find(item=>item.key==='theme');
        if(selected){localStorage.setItem('theme-studio.template',String(selected.payload.id));if(selected.accent)localStorage.setItem('theme-studio.accent',selected.accent);}
      }
      if(kind!=='apply'){localStorage.removeItem('theme-studio.template');localStorage.removeItem('theme-studio.accent');}
      appearanceDraft.clear();
      document.dispatchEvent(new CustomEvent('theme-studio-appearance-complete'));
      document.dispatchEvent(new CustomEvent('theme-studio-template-applied',{detail:{accent:localStorage.getItem('theme-studio.accent')||'#7967c6'}}));
      document.dispatchEvent(new CustomEvent('theme-studio-wallpaper-changed'));
      document.dispatchEvent(new CustomEvent('theme-studio-runtime-state'));
      setMessage(result.message||(kind==='apply'?'整套设置已应用，已保存一条恢复记录。':kind==='last'?'已恢复到上一次应用前的外观。':'已恢复使用前的可追溯外观。'));
      await refresh();
    }catch(e){setError(e instanceof Error?e.message:String(e));try{await refresh();}catch{}}
    finally{running.current=false;appearanceDraft.setBusy(false);}
  };
  const changes=appearanceDraft.list(),busy=appearanceDraft.busy;
  const invalid=changes.some(item=>item.error);
  return <section className={cs.bar} aria-label="统一应用与恢复" id="appearance-actions">
    <div className={cs.summary}><strong>{busy?'正在处理外观设置…':changes.length?`待应用 ${changes.length} 项`:'在上方选择主题或调整各区域设置'}</strong>
      <div className={cs.changes}>{changes.map(change=><span key={change.key} title={change.error}>{change.error?'⚠ ':''}{change.label}</span>)}</div>
      {state?.baselineLabel&&<small>{state.baselineLabel}</small>}
    </div>
    <div className={cs.buttons}>
      <button data-testid="apply-appearance" className={cs.primary} disabled={!native||busy||!changes.length||invalid||!!state?.pending} onClick={()=>void run('apply')}>应用当前主题</button>
      <button disabled={!native||busy||!state?.canUndo} title={state?.lastLabel} onClick={()=>void run('last')}>{state?.pending?'恢复未完成操作':'恢复上一次'}</button>
      <button disabled={!native||busy||!state?.canRestoreInitial||!!state?.pending} onClick={()=>void run('initial')}>恢复使用前外观</button>
      {!!changes.length&&<button disabled={busy} onClick={()=>{appearanceDraft.clear();document.dispatchEvent(new CustomEvent('theme-studio-draft-discarded'));}}>取消待应用</button>}
    </div>
    {invalid&&<p role="alert" className={cs.error}>{changes.filter(x=>x.error).map(x=>x.error).join('；')}</p>}
    {message&&<p role="status">{message}</p>}{error&&<p role="alert" className={cs.error}>{error}</p>}
  </section>;
}
