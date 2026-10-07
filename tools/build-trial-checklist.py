"""Generate the offline NoSeelen trial checklist from shipped feature/catalog data."""
from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parents[1]
items = []

def add(group, name, steps, expected, condition=''):
    items.append(dict(id=f'feature-{len(items)+1:03}', group=group, name=name,
                      steps=steps, expected=expected, condition=condition))

for name, steps, expected in [
 ('独立安装','安装 NoSeelen 体验版，检查开始菜单与安装目录。','显示独立体验版名称，默认目录为 ThemeStudio-NoSeelen。'),
 ('首次打开','打开后先不点应用，观察当前桌面。','只读取现状，原鼠标、图标、壁纸保持不变。'),
 ('浅色 / 深色','点击窗口顶部的浅色或深色按钮。','设置窗口配色切换；不等于修改整个 Windows 的主题。'),
 ('中文 / English','切换顶部语言，再切回中文。','已有双语区域切换；部分新增功能目前仍以中文显示。'),
 ('导航与折叠','点击左侧各入口，并折叠、展开导航。','定位到对应功能；没有 Seelen 外观、Dock 或 Mac 桌面切换入口。'),
 ('打开试用清单','进入左侧试用清单，再打开完整清单。','本离线页面可打开，并能保存每项试用结果。'),
 ('关闭后再打开','关闭设置窗口，再从开始菜单打开。','已保存配置还在；已应用的壁纸/模组按原有规则继续工作。'),
]: add('开始与界面',name,steps,expected)

for name, steps, expected in [
 ('主题大图预览','点击任意套装的查看预览。','壁纸、图标、鼠标素材可查看；预览本身不改变系统。'),
 ('主题中的资源管理器预览','在套装预览中切到文件资源管理器。','能预览背景，并调整图片可见度。'),
 ('只选择主题','点击选择此主题，暂不点击底部应用。','底部显示待应用，系统外观尚未变化。'),
 ('仅应用壁纸','取消鼠标、图标和资源管理器勾选，选择主题并统一应用。','只改变壁纸，其余项目保持现状。'),
 ('主题配套鼠标','勾选鼠标指针后选择主题并应用。','对应鼠标方案被应用，可用恢复上一次撤销。'),
 ('主题配套图标','勾选匹配的桌面图标，核对匹配结果后应用。','只替换能匹配的快捷方式图标。'),
 ('联动资源管理器','勾选同时应用主题到文件资源管理器，再统一应用。','真实 Explorer 使用对应主题静态背景，需另行检查视觉效果。'),
 ('导入主题数据包','导入有效的 .tspack 或 .zip。','套装加入列表；导入本身不改变桌面。'),
 ('导出主题数据包','在套装预览中导出，再重新导入。','导出的包包含该套装资源，可被重新识别。'),
 ('含动态版的数据包','导入带视频的套装，选择动态壁纸。','支持动态模式；只有静态资源的套装使用静态壁纸。'),
]: add('主题套装',name,steps,expected)
packs=json.loads((ROOT/'assets/templates/catalog.json').read_text(encoding='utf-8-sig'))
for pack in packs:
    add('内置主题逐套体验',pack['name']+' · '+pack.get('subtitle',''),
        '查看预览，选择所需配件，统一应用；体验后恢复上一次。',
        '核对壁纸、已勾选鼠标、匹配图标及资源管理器效果。内置套装为静态；未勾选的配件不应变化。')

for name, steps, expected in [
 ('读取当前鼠标','点击重新读取系统指针。','显示当前方案与 17 种角色。'),
 ('系统与已保存方案','在方案下拉列表里选择不同方案。','预览和草稿改变，统一应用后才改变系统。'),
 ('批量导入 CUR / ANI','选择一组 CUR 或 ANI 文件。','按文件名匹配角色；未匹配的状态保留原选择。'),
 ('单个状态替换','只为一个角色选择指针文件，再应用。','只有相应角色改变。'),
 ('大小调整','尝试 32、64、96 等尺寸，再应用。','支持 32–256、步长 16；不同程序的实际显示可能受系统缩放影响。'),
 ('保存指针方案','输入方案名并保存，重开后选中。','方案可复用；保存本身不应用到系统。'),
 ('单角色默认指针','为一个角色选择默认指针，统一应用。','该角色回到系统默认选择。'),
 ('本机天选姬方案','若出现选择天选姬方案按钮，选择并统一应用。','使用本机 ASUS 原厂资源；没有原厂资源的电脑不提供此项。'),
 ('动态指针播放','导入 ANI 并应用，在匹配场景触发。','动态角色正常播放；程序自绘光标可能不跟随。'),
]: add('鼠标指针',name,steps,expected)
module=ast.parse((ROOT/'components/icon-workbench/cursor_adapter.py').read_text(encoding='utf-8'))
roles=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROLES' for t in n.targets))
for key,name,_ in roles:
    add('17 种鼠标状态',name+' / '+key,'检查预览；在能够触发该角色的程序或操作中核对。',
        '图案、尺寸、热点与动画符合预期。不是每种状态都能在任意程序里触发。')

for name, steps, expected in [
 ('刷新与搜索快捷方式','刷新列表，输入名称搜索。','列出受支持的 .lnk / .url；此电脑、回收站、普通文件夹不在该列表。'),
 ('勾选与取消','勾选单项、勾选搜索结果、取消勾选。','只把选中的项目加入本次操作。'),
 ('导入图标图片','导入 PNG/JPG/WebP/BMP/GIF/TIFF/ICO 等支持格式。','素材进入库，预览可见；动图图标使用一帧。'),
 ('逐项配对','给两个不同快捷方式分别选择两张图片。','每个项目与自己的图片对应，不能串配。'),
 ('拖拽配对','把资源库图片拖到对应项目。','配对预览更新。'),
 ('保存对应关系','保存配对，刷新或重开后检查。','配对保留；保存不直接改变系统图标。'),
 ('统一应用图标','勾选本次应用包含已选图标，点击底部应用。','对应快捷方式图标改变；原目标地址/程序参数不变。'),
 ('缺失配对提示','选择项目但不配图片，尝试加入应用。','提示缺少配对，不把空值应用到桌面。'),
]: add('快捷方式图标',name,steps,expected)

for name, steps, expected in [
 ('本地静态图片','导入图片，先预览，再作为桌面背景加入统一应用。','真实桌面显示图片；无视差的静态图使用静态壁纸路径。'),
 ('GIF / 动态 WebP / APNG','导入可被 WebView2 解码的动图，再应用。','视差关闭时仍保持动画；不支持的编码应报错。'),
 ('本地视频','选择可播放的视频，预览后应用。','真实桌面播放，关闭设置窗口后可继续。'),
 ('示例图片与视频','分别选择内置示例。','两个示例都能预览，便于排除自备素材编码问题。'),
 ('暂停 / 继续预览','对视频或动图点击预览暂停，再继续。','预览播放状态切换。'),
 ('开启 / 关闭视差','移动鼠标，对比开启和关闭。','开启后画面平滑移动；关闭后素材仍可显示或播放。'),
 ('四种运动预设','逐个试 Elegance、Silk、Depth、Cinema。','运动幅度和跟随感有差异。'),
 ('位移强度','调整强度，移动鼠标比较。','位移幅度随设置改变。'),
 ('透视与倾角','切换透视倾斜并调整最大倾角。','倾斜强度改变，画面边缘保持覆盖。'),
 ('正向 / 反向','切换与鼠标反向移动。','视差方向相应改变。'),
 ('桌面暂停 / 继续','把桌面暂停或继续操作加入统一应用。','真实桌面播放状态改变，而不仅是窗口预览。'),
 ('停止并恢复壁纸','选择停止桌面背景，通过底部统一应用。','停止当前背景层并显示可恢复的原壁纸。'),
 ('多显示器体验','若有多屏，分别移动鼠标、检查每屏覆盖。','每屏背景位置正确；多屏实际硬件兼容性由此次体验确认。'),
]: add('壁纸与视差',name,steps,expected)

for name, steps, expected in [
 ('背景主题选择','在资源管理器区域切换背景主题。','仅预览与待应用改变。'),
 ('图片可见度','拖动图片可见度滑条，从 10% 调至 70%。','预览同步变化；应用后在真实 Explorer 比较。'),
 ('首次编译与应用','统一应用资源管理器设置并等待完成。','模块编译、启用并显示状态，随后打开真实资源管理器。'),
 ('文件列表与空白处','打开实际文件夹，切换图标视图与详细信息视图。','背景可见、文件名清楚、选中与悬停状态保留。'),
 ('导航栏与预览窗格','检查左侧导航栏及无文件可预览的窗格。','普通区域没有不期望的白色覆盖，当前选中项仍可识别。'),
 ('表头、滚动条与分隔','检查名称排序列、表头悬停、两侧分隔及滚动条。','文字清晰，白块/白线等原问题未出现。'),
 ('载入状态与实际效果','点击刷新状态，并同时观察真实 Explorer。','分别记录已启用、已载入、视觉结果；载入状态不能代替视觉验收。'),
 ('恢复 Explorer 外观','应用后使用恢复上一次。','回到这次操作前的资源管理器配置与运行状态。'),
]: add('文件资源管理器',name,steps,expected,'Windows 11 build 22621 或更新；不同系统控件可能表现不同。')

for name, steps, expected in [
 ('搜索与筛选模组','搜索名称、描述或目标程序，再切换只显示已选。','结果随筛选变化；可继续加载更多。'),
 ('选择与预设','只选一个目标明确的模组；有预设下拉框时选择预设。','形成待应用草稿，不立即改变系统。'),
 ('源码与许可','打开模组来源链接并核对作者、版本。','可追溯到相应源码。'),
 ('编译、启用、载入','统一应用一个模组，打开它的目标程序。','分别观察编译结果、启用状态、载入状态和实际功能。'),
 ('取消已选模组','取消勾选已启用模组后统一应用。','被本分支管理的该模组停用，专用 Explorer 模组单独管理。'),
 ('任务栏类模组','确认没有其他 Windhawk 引擎运行，选择一个任务栏模组。','本分支不再因 Seelen 占用任务栏而禁用选择；实际兼容性需验证。'),
 ('模组组合配置','命名、保存、导出 JSON，之后再导入。','配置回到草稿；不会因导入而自动运行模组。'),
]: add('Windhawk 扩展',name,steps,expected,'一次先试一个；通用界面提供选择与现有预设，不等于提供每个模组的完整高级设置编辑器。')

for name, steps, expected in [
 ('桌宠来源入口','查看桌宠来源卡片。','跳到原项目发布页；本包不内置桌宠角色或引擎。'),
 ('导入桌宠 EXE','选已安装或已解压桌宠的主程序。','只登记原文件路径，不移动或自动启动。'),
 ('启动与状态','点击启动桌宠，之后刷新查看。','由对应桌宠程序运行，交互由它自身提供。'),
 ('移除桌宠记录','移除已导入记录。','仅移除本软件记录，不删除原桌宠文件。'),
]: add('桌宠入口',name,steps,expected,'需自行准备桌宠主程序；不要选择安装器。')

for name, steps, expected in [
 ('多区域统一应用','同时选择主题、鼠标或图标等，再点击底部应用当前主题。','统一执行并生成一条恢复记录。'),
 ('取消待应用','做几个选择后点击取消待应用。','清空草稿，不改变系统。'),
 ('恢复上一次','连续应用两次，再逐次恢复。','按整次应用顺序撤销。'),
 ('恢复使用前外观','完成若干试用后点击恢复使用前外观。','按本分支首次记录的基线恢复；不把 Windows 默认冒充原外观。'),
 ('冲突与失败提示','若素材缺失或系统已被其他软件修改，查看提示。','保留明确错误/恢复记录，不应把失败当作成功。'),
 ('独立数据保留','关闭并重开分支，检查导入素材和记录。','使用 ThemeStudio-NoSeelen 独立目录，不继承主线试用历史。'),
 ('卸载体验分支','需要结束体验时先恢复外观，再从已安装应用卸载本分支。','仅卸载本分支程序；素材和恢复记录保留，主线程序仍在。'),
]: add('应用、恢复与结束体验',name,steps,expected)

catalog=json.loads((ROOT/'vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/catalog.json').read_text(encoding='utf-8-sig'))
mods=[]
for m in catalog['mods']:
    internal=m['id'] in {'windows-11-file-explorer-styler','themestudio-explorer-background'}
    mods.append(dict(id='mod-'+m['id'],group='模组完整目录',name=m['name'],code=m['id'],steps=m['description'],
        expected='目标程序：'+(', '.join(m['include']) or '按模组源码定义')+'；版本 '+m['version'],
        condition='由资源管理器页面管理，不在通用列表重复选择。' if internal else '通用列表可选择；兼容性与实际效果待逐项体验。',
        source=m['source'],internal=internal,presets=m['themeChoices']))
data=dict(version='0.6.4 / NoSeelen 体验版 1',branch='experiment/no-seelen-20261007',
          mainFeatures=items,mods=mods,excluded=['Seelen Dock / 顶部栏','Mac 桌面切换','Seelen 专属主题与图标包','主线应用更新通道（避免跨分支覆盖）'])
out=ROOT/'docs/guide';out.mkdir(parents=True,exist_ok=True)
(out/'trial-features.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ThemeStudio · 全部功能试用清单</title><link rel="icon" href="data:,">
<style>*{box-sizing:border-box}body{margin:0;background:#f4f5fa;color:#22273b;font:15px/1.65 "Microsoft YaHei UI",sans-serif}header,main{max-width:1180px;margin:auto;padding:28px}header{padding-bottom:12px}h1{font-size:32px;margin:6px 0}h2{font-size:20px}p{margin:8px 0}.eyebrow{color:#6257a2;letter-spacing:2px;font-size:12px}.summary,.tools,.item{background:white;border:1px solid #e0e3ef;border-radius:12px;padding:18px}.summary{border-left:5px solid #7862c6}.tools{position:sticky;top:8px;z-index:1;display:flex;gap:10px;flex-wrap:wrap;box-shadow:0 4px 18px #24203a0a}button,input,select,textarea{font:inherit;border:1px solid #ccd1e0;border-radius:6px;padding:7px 10px;background:white;color:inherit}button{cursor:pointer}input[type=search]{flex:1;min-width:180px}progress{width:170px;accent-color:#7862c6}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.item h3{margin:0 0 8px;font-size:16px}.item .condition{font-size:13px;color:#79602b;background:#fff9e9;padding:7px 10px;border-radius:6px}.item textarea{width:100%;height:62px;margin-top:10px;resize:vertical}.label{color:#61697e;font-size:12px}.status{float:right;max-width:125px;margin-left:10px}details{margin-top:24px}summary{cursor:pointer;font-size:21px;font-weight:bold}.id{font-size:11px;color:#8a8e9d}footer{color:#777;padding:30px 0}#toast{color:#6752a0}.empty{padding:30px}a{color:#6252ad} @media(max-width:700px){.grid{grid-template-columns:1fr}header,main{padding:16px}h1{font-size:25px}}@media print{.tools,button,textarea{display:none}.grid{display:block}.item{break-inside:avoid;margin:10px 0}details{display:block}}</style>
<header><div class="eyebrow">THEME STUDIO / NOSEELEN / TRIAL 1</div><h1>一项一项试，再决定主线</h1><p>基于 0.6.4 的独立实验分支 · 2026-10-07</p><div class="summary"><strong>先试鼠标 → 壁纸 → 图标 → 主题 → 资源管理器 → 可选模组。</strong><p>每项可标记正常、有问题或不需要，并记录现象。结果保存在此浏览器本地，也可导出 JSON。清单不会操作你的桌面。</p><p>安装与数据目录独立，但两版修改的是同一个 Windows 桌面。请逐版体验，先恢复再切换。当前没有逐项替你判定视觉合格。</p><p id="scope"></p></div></header>
<main><div class="tools"><input id="search" type="search" placeholder="搜索功能、模组、目标程序"><select id="filter"><option value="all">全部状态</option><option value="todo">待试用</option><option value="ok">正常</option><option value="issue">有问题</option><option value="skip">不需要 / 无条件</option></select><button id="export">导出结果</button><button id="import">导入结果</button><input type="file" id="import-file" accept=".json" hidden><span id="count"></span><progress id="progress"></progress></div><p id="toast" role="status"></p><div id="features"></div><details id="mod-details"><summary id="mod-title"></summary><p>完整目录包含两个由资源管理器页面管理的内部模块。其余模组只提供源码与选择能力，尚未逐项验证；不建议一次启用一批。每个模组的运行条件以其源码为准。</p><div id="mods" class="grid"></div></details><footer>本分支保留已复用媒体、界面和运动算法的来源与许可证。Seelen 运行引擎、Dock、顶部工具栏及专属主题功能已移除。</footer></main>
<script type="application/json" id="data">__DATA__</script><script>
const data=JSON.parse(document.getElementById('data').textContent),all=[...data.mainFeatures,...data.mods],key='themestudio-no-seelen-trial1-results';let saved={};try{saved=JSON.parse(localStorage.getItem(key)||'{}')}catch{}const $=id=>document.getElementById(id);const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const labels={todo:'待试用',ok:'正常',issue:'有问题',skip:'不需要 / 无条件'};
function save(){try{localStorage.setItem(key,JSON.stringify(saved));$('toast').textContent='结果已保存在此浏览器。'}catch{$('toast').textContent='浏览器未允许本地保存，请及时导出结果。'}stats()}
function stats(){const done=all.filter(i=>saved[i.id]?.status&&saved[i.id].status!=='todo').length;$('count').textContent=`已记录 ${done} / ${all.length}`;$('progress').max=all.length;$('progress').value=done}
function matches(i){const q=$('search').value.trim().toLowerCase(),f=$('filter').value;return (!q||[i.name,i.code,i.group,i.steps,i.expected].join(' ').toLowerCase().includes(q))&&(f==='all'||(saved[i.id]?.status||'todo')===f)}
function card(i){const r=saved[i.id]||{};return `<article class="item" data-id="${escape(i.id)}"><select class="status" aria-label="${escape(i.name)} 试用结果">${Object.entries(labels).map(([v,l])=>`<option value="${v}" ${v===(r.status||'todo')?'selected':''}>${l}</option>`).join('')}</select><span class="id">${escape(i.code||i.id)}</span><h3>${escape(i.name)}</h3><div class="label">怎么试</div><p>${escape(i.steps)}</p><div class="label">应看到什么</div><p>${escape(i.expected)}</p>${i.condition?`<p class="condition">${escape(i.condition)}</p>`:''}${i.source?`<a href="${escape(i.source)}" target="_blank" rel="noopener noreferrer">查看源码与条件 ↗</a>`:''}${i.presets?.length?`<p>已有预设：${i.presets.map(p=>escape(p.label)).join('、')}</p>`:''}<textarea aria-label="${escape(i.name)} 备注" placeholder="记录看到的效果、问题、是否需要保留…">${escape(r.note||'')}</textarea></article>`}
function render(){const groups=[...new Set(data.mainFeatures.map(i=>i.group))];$('features').innerHTML=groups.map(g=>{const rows=data.mainFeatures.filter(i=>i.group===g&&matches(i));return rows.length?`<section><h2>${escape(g)} <small>· ${rows.length}</small></h2><div class="grid">${rows.map(card).join('')}</div></section>`:''}).join('')||'<p class="empty">日常功能没有匹配结果。</p>';const mods=data.mods.filter(matches);$('mod-title').textContent=`Windhawk 完整目录 · ${mods.length} / ${data.mods.length}`;$('mods').innerHTML=$('mod-details').open?mods.map(card).join(''):'';stats()}
document.addEventListener('change',e=>{const a=e.target.closest('article[data-id]');if(a&&e.target.matches('select.status')){saved[a.dataset.id]={...saved[a.dataset.id],status:e.target.value};save()}});document.addEventListener('input',e=>{const a=e.target.closest('article[data-id]');if(a&&e.target.matches('textarea')){saved[a.dataset.id]={...saved[a.dataset.id],note:e.target.value};save()}});$('search').oninput=render;$('filter').onchange=render;$('mod-details').ontoggle=render;
$('export').onclick=()=>{const record={version:data.version,branch:data.branch,exportedAt:new Date().toISOString(),results:all.map(i=>({id:i.id,name:i.name,group:i.group,status:saved[i.id]?.status||'todo',note:saved[i.id]?.note||''}))};const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='ThemeStudio-NoSeelen-试用结果.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000)};
$('import').onclick=()=>$('import-file').click();$('import-file').onchange=async e=>{try{const f=e.target.files[0];if(!f||f.size>2*1024*1024)throw Error('请选择小于 2 MB 的结果文件');const record=JSON.parse(await f.text());if(record.branch!==data.branch||!Array.isArray(record.results))throw Error('这不是本分支的试用结果');const valid=new Set(all.map(i=>i.id));for(const r of record.results){if(valid.has(r.id)&&Object.hasOwn(labels,r.status)&&typeof r.note==='string')saved[r.id]={status:r.status,note:r.note.slice(0,20000)}}save();render()}catch(err){$('toast').textContent=String(err)}e.target.value=''};
$('scope').textContent=`清单包含 ${data.mainFeatures.length} 项日常功能与检查点、${data.mods.length} 项模组记录（${data.mods.filter(m=>!m.internal).length} 项在通用列表可选）。移除：${data.excluded.join('；')}。`;render();
</script></html>'''
html=html.replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
(out/'trial-checklist.html').write_text(html,encoding='utf-8')
lines=['ThemeStudio 0.6.4 · NoSeelen 体验版 1：全部功能试用清单',
       '分支：experiment/no-seelen-20261007','HTML 版可标记状态、记备注及导出结果。','']
last=None
for i in items:
    if i['group']!=last: lines.extend(['',i['group']]);last=i['group']
    lines.extend([f"[ ] {i['id']} {i['name']}",f"    操作：{i['steps']}",f"    预期：{i['expected']}"])
    if i['condition']:lines.append('    条件：'+i['condition'])
lines.extend(['','Windhawk 完整目录（内部模块另注；未逐项验证兼容性）'])
for m in mods:lines.append(f"[ ] {m['code']} | {m['name']} | {m['steps']} | {m['condition']}")
(out/'trial-checklist.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'mainFeatures':len(items),'mods':len(mods),'genericSelectableMods':sum(not m['internal'] for m in mods),'bundledThemes':len(packs)},ensure_ascii=False))
