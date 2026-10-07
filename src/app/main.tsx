// SPDX-License-Identifier: AGPL-3.0-or-later
import { render } from "preact";
import { useEffect, useState } from "preact/hooks";
import { ConfigProvider, theme } from "antd";
import i18n from "i18next";
import { I18nextProvider, initReactI18next } from "react-i18next";
import yaml from "js-yaml";
import { WorkbenchView } from "../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/infra/View.tsx";
import { NavigationFrame } from "../../vendor/Seelen-UI/src/ui/react/settings/components/navigation/NavigationFrame.tsx";
import ModCardFrame from "../../vendor/windhawk/src/windhawk-frontend/apps/windhawk-frontend/src/app/panel/shared/ModCardFrame.tsx";
import { parseRecipe, type ThemeRecipe } from "../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/model.ts";
import catalog from "../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/catalog.json";
import enYaml from "../../vendor/Seelen-UI/src/ui/react/settings/i18n/translations/workbench.en.yml";
import zhYaml from "../../vendor/Seelen-UI/src/ui/react/settings/i18n/translations/workbench.zh-CN.yml";
import { isDesktopApp, studioClient } from "./bridge.ts";
import "../../vendor/Seelen-UI/libs/core/styles/spacings.css";
import "../../vendor/Seelen-UI/libs/core/styles/colors.css";
import "../../vendor/Seelen-UI/src/ui/react/settings/styles/variables.css";
import cs from "./studio.module.css";
import { RuntimePanel, type RuntimeState } from "./runtime.tsx";
import { TemplateLibrary } from "./templates.tsx";
import { ExplorerPanel } from "./explorer.tsx";
import { PetPanel } from "./pets.tsx";
import { AppearanceBar } from './appearance.tsx';
import { appearanceDraft } from '../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/appearance.ts';

const messages = {
  "zh-CN": { name: "桌面主题工作室 · 体验分支", subtitle: "让桌面，成为你的样子", native: "桌面应用", local: "本机开发", collapse: "展开或收起导航", desktop: "桌面图标", cursors: "鼠标指针", parallax: "壁纸与视差", seelen: "Seelen 外观", windhawk: "Windhawk 模组", source: "查看源码", draft: "待启用", appearance: "外观", light: "浅色", dark: "深色", scope: "逐项对应图片与桌面图标；把图片和视频应用到桌面；选择资源管理器样式和 Windows 模组。", about: "日常外观管理 · 独立体验", version: "v0.6.4 · NoSeelen 体验版 1" },
  en: { name: "Theme Studio · Trial branch", subtitle: "Make your desktop your own", native: "Desktop app", local: "Local development", collapse: "Expand or collapse navigation", desktop: "Desktop icons", cursors: "Mouse pointers", parallax: "Wallpaper & parallax", seelen: "Seelen appearance", windhawk: "Windhawk mods", source: "View source", draft: "Pending activation", appearance: "Appearance", light: "Light", dark: "Dark", scope: "Pair pictures with individual shortcuts, apply images and videos to the desktop, and customize Explorer with selected Windows mods.", about: "Everyday appearance · Trial", version: "v0.6.4 · NoSeelen trial 1" },
};
await i18n.use(initReactI18next).init({ lng: localStorage.getItem("theme-studio.language") || "zh-CN", fallbackLng: "en", interpolation: { escapeValue: false }, resources: {
  en: { translation: { ...(yaml.load(enYaml) as object), studio: messages.en } },
  "zh-CN": { translation: { ...(yaml.load(zhYaml) as object), studio: messages["zh-CN"] } },
} });
i18n.addResourceBundle("zh-CN", "translation", { theme_workbench: { windhawk_notice: "选择模组和预设后，通过底部“应用当前主题”统一启用。取消勾选后再次应用可停用。", draft_saved: "组合草稿已保存，可通过底部入口统一应用。", runtime: { notice: "模组需要目标程序运行才能显示效果。取消勾选并统一应用可停用；载入状态不能代替实际效果检查。" } } }, true, true);
i18n.addResourceBundle("en", "translation", { theme_workbench: { windhawk_notice: "Select mods and presets, then use the shared Apply button. Deselect and apply again to disable them.", draft_saved: "Draft saved. Use the shared Apply button when ready.", runtime: { notice: "Mods require their target applications. Deselect and apply to disable. Loaded status does not verify visual results." } } }, true, true);
let initial: ThemeRecipe = { schemaVersion: 1, name: "我的桌面主题", seelen: { activeThemes: [], activeIconPacks: [] }, windhawk: [] };
const stored = localStorage.getItem("theme-studio.recipe.v1");
if (stored) { try { initial = parseRecipe(stored); } catch { /* Keep unreadable storage untouched. */ } }
// Explorer styling has its own apply/undo controls in 0.6.0.
initial = {...initial, seelen: {activeThemes: initial.seelen.activeThemes.filter(id=>id==="@workbench/wallpaper-parallax"), activeIconPacks: []}, windhawk: initial.windhawk.filter(mod=>!['windows-11-file-explorer-styler','themestudio-explorer-background'].includes(mod.id))};

function Studio() {
  const [,draftRevision]=useState(0);
  useEffect(()=>appearanceDraft.subscribe(()=>draftRevision(n=>n+1)),[]);
  const [language, setLanguage] = useState(i18n.language === "en" ? "en" : "zh-CN");
  const [dark, setDark] = useState(localStorage.getItem("theme-studio.dark") === "true");
  const [active, setActive] = useState("templates");
  const [accent, setAccent] = useState(localStorage.getItem("theme-studio.accent") || "#7967c6");
  const [runtimes, setRuntimes] = useState<RuntimeState | null>(null);
  const text = messages[language as keyof typeof messages];
  const items = [
    { id: "templates", label: language === "en" ? "Theme collections" : "一键主题", icon: "◈" },
    { id: "explorer", label: language === "en" ? "File Explorer" : "文件资源管理器", icon: "▤" },
    { id: "pets", label: language === "en" ? "Desktop pets" : "桌宠", icon: "♧" },
    { id: "desktop", label: text.desktop, icon: "▦" }, { id: "cursors", label: text.cursors, icon: "↖" },
    { id: "parallax", label: text.parallax, icon: "▧" },
    { id: "windhawk", label: text.windhawk, icon: "✦" },
    { id: "trial", label: language === "en" ? "Trial checklist" : "试用清单", icon: "☑" },
  ];
  useEffect(() => {
    const update = (event: Event) => setAccent((event as CustomEvent<{accent:string}>).detail.accent);
    document.addEventListener("theme-studio-template-applied", update);
    return () => document.removeEventListener("theme-studio-template-applied", update);
  }, []);
  useEffect(() => {
    document.documentElement.style.colorScheme = dark ? "dark" : "light";
    document.title = text.name;
    localStorage.setItem("theme-studio.dark", String(dark));
  }, [dark, language]);
  useEffect(() => {
    const sections = items.map((item) => document.getElementById(`workbench-${item.id}`)).filter((s): s is HTMLElement => !!s);
    const observer = new IntersectionObserver((entries) => {
      const entry = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (entry) setActive(entry.target.id.replace("workbench-", ""));
    }, { root: document.getElementById("studio-content"), rootMargin: "-5% 0px -60% 0px" });
    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);
  return <I18nextProvider i18n={i18n}><ConfigProvider theme={{ token: { colorPrimary: accent, borderRadius: 9, fontFamily: "Microsoft YaHei UI, Segoe UI, sans-serif" }, algorithm: dark ? theme.darkAlgorithm : theme.defaultAlgorithm }}>
    <div className={cs.shell}>
      <NavigationFrame title={language === 'en' ? 'Theme Studio' : '主题工作室'} items={items} active={active} collapseLabel={text.collapse} onSelect={(id) => { setActive(id); document.getElementById(`workbench-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" }); }}
        footer={<><span className={cs.sourceNote}>{text.about}</span><span className={cs.version}>{text.version}</span></>} />
      <div className={cs.workspace}>
        <header className={cs.header}><div><h1>{text.name}</h1><p>{text.subtitle}</p></div><span className={cs.runtime}>{isDesktopApp ? text.native : text.local}</span>
          <a href="/help/index.html" target="_blank" rel="noopener noreferrer">{language === "en" ? "User guide" : "图文教程"}</a>
          <button onClick={() => setDark(!dark)} aria-label={text.appearance}>{dark ? "☀ " + text.light : "☾ " + text.dark}</button>
          <button onClick={() => { const next = language === "en" ? "zh-CN" : "en"; setLanguage(next); localStorage.setItem("theme-studio.language", next); void i18n.changeLanguage(next); }}>{language === "en" ? "中文" : "English"}</button>
        </header>
        <main id="studio-content" className={cs.content}>
          <fieldset disabled={appearanceDraft.busy} style={{border:0,padding:0,margin:0,minWidth:0}}>
          <p className={cs.scope}>{text.scope}</p>
          <TemplateLibrary client={studioClient} native={isDesktopApp} />
          <ExplorerPanel client={studioClient} native={isDesktopApp} />
          <PetPanel client={studioClient} native={isDesktopApp} />
          <WorkbenchView embedded unified showSeelen={false} initial={initial} native={isDesktopApp} desktopClient={studioClient} mods={catalog.mods.filter(mod=>!['windows-11-file-explorer-styler','themestudio-explorer-background'].includes(mod.id))}
            themes={[{ id: "@workbench/wallpaper-parallax", name: text.parallax }]}
            icons={[]}
            onExport={async (recipe) => (await studioClient.call<{ path: string }>("recipe.export", recipe)).path}
            renderRuntime={(recipe) => <RuntimePanel client={studioClient} recipe={recipe} native={isDesktopApp} onState={setRuntimes} unified />}
            renderMod={(mod, selected, onSelect, onTheme) => <div className={cs.mod}>
              <ModCardFrame id={mod.id} title={mod.name} description={mod.description} selected={!!selected} onSelect={onSelect} selectLabel={i18n.t("theme_workbench.select_mod", { name: mod.name })}
                ribbon={runtimes?.windhawk.mods.find((item) => item.id === `local@${mod.id}`)?.enabled ? i18n.t("theme_workbench.runtime.mod_enabled") : selected ? text.draft : undefined} metadata={<small className={cs.metadata}>{mod.author} · {mod.version}</small>}
                actions={<><small>{mod.license}</small><a href={mod.source} target="_blank" rel="noopener noreferrer">{text.source}</a></>} />
              {!!mod.themeChoices.length && <select aria-label={i18n.t("theme_workbench.preset", { name: mod.name })} disabled={!selected} value={String(selected?.settings.theme || "")} onChange={(e) => onTheme(e.currentTarget.value)}>
                <option value="" disabled>{i18n.t("theme_workbench.choose_preset")}</option>{mod.themeChoices.map((choice) => <option key={choice.id} value={choice.id}>{choice.label}</option>)}
              </select>}
            </div>} />
          <section id="workbench-trial" className={cs.enginePanel}>
            <h2>{language === 'en' ? 'Trial checklist' : '逐项试用清单'}</h2>
            <p>{language === 'en' ? 'Independent profile. Mainline updates are disabled for this experiment.' : '本分支使用独立数据目录。体验完成前不接收主线更新。'}</p>
            <a href="/help/trial-checklist.html" target="_blank" rel="noopener noreferrer">{language === 'en' ? 'Open all features and record results' : '打开全部功能清单，逐项记录试用结果'}</a>
          </section>
          </fieldset>
        </main>
        <AppearanceBar client={studioClient} native={isDesktopApp}/>
      </div>
    </div>
  </ConfigProvider></I18nextProvider>;
}
render(<Studio />, document.getElementById("root")!);
