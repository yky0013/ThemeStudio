// Runs the same settings component as the native Seelen route; no mock native API.
import { render } from "preact";
import { useState } from "preact/hooks";
import { ConfigProvider, theme, Button } from "antd";
import i18n from "i18next";
import { I18nextProvider, initReactI18next } from "react-i18next";
import yaml from "js-yaml";
import { WorkbenchView } from "../../src/ui/react/settings/modules/themeWorkbench/infra/View.tsx";
import { parseRecipe } from "../../src/ui/react/settings/modules/themeWorkbench/domain/model.ts";
import { createDesktopClient } from "../../src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts";
import type { ThemeRecipe } from "../../src/ui/react/settings/modules/themeWorkbench/domain/model.ts";
import catalog from "../../src/ui/react/settings/modules/themeWorkbench/domain/catalog.json";
import en from "../../src/ui/react/settings/i18n/translations/workbench.en.yml";
import zh from "../../src/ui/react/settings/i18n/translations/workbench.zh-CN.yml";
import "../../libs/core/styles/spacings.css";
import "../../libs/core/styles/colors.css";
import "../../src/ui/react/settings/styles/variables.css";

await i18n.use(initReactI18next).init({ lng: "zh-CN", fallbackLng: "en", interpolation: { escapeValue: false },
  resources: { en: { translation: yaml.load(en) }, "zh-CN": { translation: yaml.load(zh) } } as never,
});
let initial: ThemeRecipe = {
  schemaVersion: 1, name: "我的桌面主题", seelen: { activeThemes: ["@default/theme"], activeIconPacks: ["@system/icon-pack"] }, windhawk: [],
};
const stored = localStorage.getItem("theme-workbench.recipe.v1");
if (stored) { try { initial = parseRecipe(stored); } catch (error) { console.warn("Saved recipe was preserved but could not be loaded", error); } }
const themes = [
  { id: "@default/theme", name: "Seelen 默认主题", description: "Seelen 源码自带的基础样式" },
  { id: "@eythaann/bubbles", name: "Bubbles", description: "Seelen 源码自带的气泡风格主题" },
  { id: "@workbench/wallpaper-parallax", name: "壁纸与鼠标视差", description: "在同一层图片或视频上叠加平滑运动和透视" },
];
const icons = [{ id: "@system/icon-pack", name: "系统图标", description: "使用应用原有图标" }];
const desktopClient = createDesktopClient();

function Preview() {
  const [dark, setDark] = useState(false);
  const [english, setEnglish] = useState(false);
  document.documentElement.style.colorScheme = dark ? "dark" : "light";
  return <I18nextProvider i18n={i18n}><ConfigProvider theme={{ token: { colorPrimary: "#7562c7", borderRadius: 9, fontFamily: "Microsoft YaHei UI, system-ui, sans-serif" }, algorithm: dark ? theme.darkAlgorithm : theme.defaultAlgorithm }}>
    <div style={{ maxWidth: 1420, margin: "0 auto", display: "flex", justifyContent: "flex-end", gap: 10, paddingBottom: 8 }}>
      <Button onClick={() => setDark(!dark)}>{dark ? "☀" : "☾"}</Button>
      <Button onClick={() => { setEnglish(!english); void i18n.changeLanguage(english ? "zh-CN" : "en"); }}>{english ? "中文" : "English"}</Button>
    </div>
    <WorkbenchView initial={initial} themes={themes} icons={icons} mods={catalog.mods} native={false} desktopClient={desktopClient} onExport={async (recipe) => {
      const response = await fetch("/export", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(recipe) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || response.statusText);
      return result.path as string;
    }} />
  </ConfigProvider></I18nextProvider>;
}
render(<Preview />, document.getElementById("root")!);
