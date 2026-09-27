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

const messages = {
  "zh-CN": { name: "桌面主题工作室", subtitle: "让桌面，成为你的样子", native: "桌面应用", local: "本机开发", collapse: "展开或收起导航", desktop: "桌面图标", cursors: "鼠标指针", parallax: "壁纸与视差", seelen: "Seelen 外观", windhawk: "Windhawk 模组", source: "查看源码", draft: "已选配置", appearance: "外观", light: "浅色", dark: "深色", scope: "图标和指针可直接应用；壁纸视差可交互预览，Seelen 外观与 Windhawk 模组保存为组合配置。", about: "基于 Seelen UI 与 Windhawk", version: "独立项目 · v0.1.1" },
  en: { name: "Theme Studio", subtitle: "Make your desktop your own", native: "Desktop app", local: "Local development", collapse: "Expand or collapse navigation", desktop: "Desktop icons", cursors: "Mouse pointers", parallax: "Wallpaper & parallax", seelen: "Seelen appearance", windhawk: "Windhawk mods", source: "View source", draft: "In draft", appearance: "Appearance", light: "Light", dark: "Dark", scope: "Icons and cursors apply to Windows. Wallpaper parallax is interactive; Seelen appearance and Windhawk mods are saved as composition settings.", about: "Based on Seelen UI and Windhawk", version: "Independent project · v0.1.1" },
};
await i18n.use(initReactI18next).init({ lng: localStorage.getItem("theme-studio.language") || "zh-CN", fallbackLng: "en", interpolation: { escapeValue: false }, resources: {
  en: { translation: { ...(yaml.load(enYaml) as object), studio: messages.en } },
  "zh-CN": { translation: { ...(yaml.load(zhYaml) as object), studio: messages["zh-CN"] } },
} });
i18n.addResourceBundle("zh-CN", "translation", { theme_workbench: { seelen_description: "选择 Seelen 主题与图标包，记录到组合配置。", draft_saved: "组合配置已保存。桌面图标和鼠标请在各自区域应用。" } }, true, true);
i18n.addResourceBundle("en", "translation", { theme_workbench: { seelen_description: "Choose Seelen themes and icon packs for the composition.", draft_saved: "Composition saved. Apply desktop icons and pointers in their own sections." } }, true, true);
let initial: ThemeRecipe = { schemaVersion: 1, name: "我的桌面主题", seelen: { activeThemes: ["@default/theme"], activeIconPacks: ["@system/icon-pack"] }, windhawk: [] };
const stored = localStorage.getItem("theme-studio.recipe.v1");
if (stored) { try { initial = parseRecipe(stored); } catch { /* Keep unreadable storage untouched. */ } }

function Studio() {
  const [language, setLanguage] = useState(i18n.language === "en" ? "en" : "zh-CN");
  const [dark, setDark] = useState(localStorage.getItem("theme-studio.dark") === "true");
  const [active, setActive] = useState("desktop");
  const text = messages[language as keyof typeof messages];
  const items = [
    { id: "desktop", label: text.desktop, icon: "▦" }, { id: "cursors", label: text.cursors, icon: "↖" },
    { id: "parallax", label: text.parallax, icon: "▧" }, { id: "seelen", label: text.seelen, icon: "◈" },
    { id: "windhawk", label: text.windhawk, icon: "✦" },
  ];
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
  return <I18nextProvider i18n={i18n}><ConfigProvider theme={{ token: { colorPrimary: "#7967c6", borderRadius: 9, fontFamily: "Microsoft YaHei UI, Segoe UI, sans-serif" }, algorithm: dark ? theme.darkAlgorithm : theme.defaultAlgorithm }}>
    <div className={cs.shell}>
      <NavigationFrame title={text.name} items={items} active={active} collapseLabel={text.collapse} onSelect={(id) => { setActive(id); document.getElementById(`workbench-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" }); }}
        footer={<><span className={cs.sourceNote}>{text.about}</span><span className={cs.version}>{text.version}</span></>} />
      <div className={cs.workspace}>
        <header className={cs.header}><div><h1>{text.name}</h1><p>{text.subtitle}</p></div><span className={cs.runtime}>{isDesktopApp ? text.native : text.local}</span>
          <a href="/help/index.html" target="_blank" rel="noopener noreferrer">{language === "en" ? "User guide" : "图文教程"}</a>
          <button onClick={() => setDark(!dark)} aria-label={text.appearance}>{dark ? "☀ " + text.light : "☾ " + text.dark}</button>
          <button onClick={() => { const next = language === "en" ? "zh-CN" : "en"; setLanguage(next); localStorage.setItem("theme-studio.language", next); void i18n.changeLanguage(next); }}>{language === "en" ? "中文" : "English"}</button>
        </header>
        <main id="studio-content" className={cs.content}>
          <p className={cs.scope}>{text.scope}</p>
          <WorkbenchView embedded initial={initial} native={false} desktopClient={studioClient} mods={catalog.mods}
            themes={[{ id: "@default/theme", name: "Seelen Default" }, { id: "@eythaann/bubbles", name: "Bubbles" }, { id: "@workbench/wallpaper-parallax", name: text.parallax }]}
            icons={[{ id: "@system/icon-pack", name: language === "en" ? "System icons" : "系统图标" }]}
            onExport={async (recipe) => (await studioClient.call<{ path: string }>("recipe.export", recipe)).path}
            renderMod={(mod, selected, onSelect, onTheme) => <div className={cs.mod}>
              <ModCardFrame id={mod.id} title={mod.name} description={mod.description} selected={!!selected} onSelect={onSelect} selectLabel={i18n.t("theme_workbench.select_mod", { name: mod.name })}
                ribbon={selected ? text.draft : undefined} metadata={<small className={cs.metadata}>{mod.author} · {mod.version}</small>}
                actions={<><small>{mod.license}</small><a href={mod.source} target="_blank" rel="noopener noreferrer">{text.source}</a></>} />
              {!!mod.themeChoices.length && <select aria-label={i18n.t("theme_workbench.preset", { name: mod.name })} disabled={!selected} value={String(selected?.settings.theme || "")} onChange={(e) => onTheme(e.currentTarget.value)}>
                <option value="" disabled>{i18n.t("theme_workbench.choose_preset")}</option>{mod.themeChoices.map((choice) => <option key={choice.id} value={choice.id}>{choice.label}</option>)}
              </select>}
            </div>} />
        </main>
      </div>
    </div>
  </ConfigProvider></I18nextProvider>;
}
render(<Studio />, document.getElementById("root")!);
