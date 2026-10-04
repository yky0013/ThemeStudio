// SPDX-License-Identifier: AGPL-3.0-or-later
import cs from './explorer-preview.module.css';

export interface ExplorerAppearance { imageOpacity: number; tint: string; }
export const defaultExplorerAppearance: ExplorerAppearance = {imageOpacity: 35, tint: '#081b32'};

/** Uses the same cover crop, dark tint and image opacity as the native renderer. */
export function ExplorerPreview({image, name, appearance = defaultExplorerAppearance}: {
  image?: string; name: string; appearance?: ExplorerAppearance;
}) {
  return <figure className={cs.figure} aria-label={`${name}资源管理器效果预览`}>
    <div className={cs.window} style={{backgroundColor: appearance.tint}}>
      {image && <img className={cs.background} src={image} alt="" style={{opacity: appearance.imageOpacity / 100}}/>}
      <div className={cs.chrome}><div className={cs.tab}>▤　文件资源管理器 <span>×</span></div><span>＋</span><span className={cs.controls}>—　□　×</span></div>
      <div className={cs.address}><span>←　→　↑</span><div>⌂　此电脑　›　文档</div><div>⌕　搜索文档</div></div>
      <div className={cs.commands}>＋ 新建 <span>✂　▣　▤</span><span>排序⌄　查看⌄　···</span></div>
      <div className={cs.body}>
        <aside className={cs.sidebar}><p>⌂　主文件夹</p><p>▧　图库</p><p>☆　收藏夹</p><hr/><p>▣　桌面</p><p>↓　下载</p><p className={cs.selected}>▤　文档</p><p>▧　图片</p><hr/><p>▰　此电脑</p></aside>
        <div className={cs.files}><div className={cs.columns}><span>名称</span><span>修改日期</span><span>类型</span></div>
          {[['项目资料','文件夹'],['图片素材','文件夹'],['研究笔记','文件夹'],['演示文稿.pptx','PowerPoint 演示文稿'],['工作记录.docx','Word 文档']].map(([file,type],i)=><div key={file} className={cs.file}><span><b className={i<3?cs.folder:cs.document}>{i<3?'▰':'▤'}</b>{file}</span><span>2026/10/4</span><span>{type}</span></div>)}
          <div className={cs.caption}>{name}<small>背景与主题一起切换</small></div>
        </div>
      </div><div className={cs.status}>5 个项目</div>
    </div><figcaption>效果预览 · 使用主题静态背景；真实工具栏和控件布局随 Windows 版本变化。</figcaption>
  </figure>;
}
