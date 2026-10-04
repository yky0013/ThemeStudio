// SPDX-License-Identifier: AGPL-3.0-or-later
export type AppearanceKey = 'theme'|'icons'|'cursors'|'wallpaper'|'explorer'|'desktop'|'seelen'|'windhawk';
export interface AppearanceChange {
  key: AppearanceKey; label: string; operation: string; payload: Record<string, unknown>;
  accent?: string; error?: string;
}

/** A local draft only. The single toolbar submits the entire plan as one transaction. */
export class AppearanceDraft {
  private changes = new Map<AppearanceKey,AppearanceChange>();
  private listeners = new Set<()=>void>();
  private locked=false;
  desktopMode='windows';
  seelen:Record<string,unknown>={activeThemes:['@default/theme'],activeIconPacks:['@system/icon-pack']};
  get effectiveDesktopMode(){return String(this.changes.get('desktop')?.payload.mode||this.desktopMode);}
  subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener);};}
  get busy(){return this.locked;}
  setBusy(value:boolean){this.locked=value;this.emit();}
  set(key:AppearanceKey, change:Omit<AppearanceChange,'key'>|null){
    if(this.locked)return;
    if(change)this.changes.set(key,{...change,key});else this.changes.delete(key);
    this.emit();
  }
  get(key:AppearanceKey){return this.changes.get(key);}
  clear(){this.changes.clear();this.emit();}
  list(){return [...this.changes.values()];}
  plan(){
    const order:AppearanceKey[]=['theme','desktop','seelen','windhawk','icons','cursors','wallpaper','explorer'];
    let plan=order.flatMap(key=>this.changes.has(key)?[{...this.changes.get(key)!,payload:{...this.changes.get(key)!.payload}}]:[]);
    const desktop=plan.find(item=>item.key==='desktop');
    if(desktop){
      plan=plan.filter(item=>item.key!=='seelen');
      if(desktop.payload.mode==='mac'){desktop.operation='runtime.seelen.apply';desktop.payload={seelen:this.seelen};}
    }
    const theme=plan.find(item=>item.key==='theme');
    if(theme){
      // A custom resource selected in its panel replaces the theme's accessory.
      if(this.changes.has('icons'))theme.payload.icons=false;
      if(this.changes.has('cursors'))theme.payload.cursors=false;
      if(this.changes.has('explorer'))theme.payload.explorer=false;
    }
    return plan;
  }
  private emit(){this.listeners.forEach(listener=>listener());}
}
export const appearanceDraft=new AppearanceDraft();
