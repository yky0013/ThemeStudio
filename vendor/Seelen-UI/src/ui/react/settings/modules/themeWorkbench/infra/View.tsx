// SPDX-License-Identifier: AGPL-3.0-or-later
import { useRef, useState } from "preact/hooks";
import type { ComponentChildren } from "preact";
import { Alert, Button, Checkbox, Select, Tag } from "antd";
import { useTranslation } from "react-i18next";
import { checkDependencies, filterMods, parseRecipe, toggleMod } from "../domain/model.ts";
import type { ModDraft, ModResource, ResourceChoice, ThemeRecipe } from "../domain/model.ts";
// Reuse Seelen's actual settings group styles rather than recreating another UI.
import groupStyles from "../../../components/SettingsBox/index.module.css";
import cs from "./index.module.css";
import { ParallaxPanel } from "./ParallaxPanel.tsx";
import { DesktopPanel } from "./DesktopPanel.tsx";
import type { DesktopClient } from "../domain/desktop.ts";
import { DEFAULT_PARALLAX, PARALLAX_THEME_ID } from "../../../../../../../libs/ui/shared/wallpaper-parallax/motion.ts";
import type { ParallaxSettings } from "../../../../../../../libs/ui/shared/wallpaper-parallax/motion.ts";

export interface WorkbenchProps {
  mods: ModResource[];
  themes: ResourceChoice[];
  icons: ResourceChoice[];
  initial: ThemeRecipe;
  native: boolean;
  onApply?: (recipe: ThemeRecipe) => Promise<void>;
  onExport?: (recipe: ThemeRecipe) => Promise<string>;
  renderSettings?: ComponentChildren;
  renderRuntime?: (recipe: ThemeRecipe) => ComponentChildren;
  desktopClient?: DesktopClient;
  embedded?: boolean;
  renderMod?: (mod: ModResource, selected: ModDraft | undefined, onSelect: (selected: boolean) => void, onTheme: (theme: string) => void) => ComponentChildren;
}

export function WorkbenchView({ mods, themes, icons, initial, native, onApply, onExport, renderSettings, renderRuntime, desktopClient, embedded, renderMod }: WorkbenchProps) {
  const { t } = useTranslation();
  const tt = (key: string, options?: Record<string, unknown>) => t(`theme_workbench.${key}`, options);
  const [recipe, setRecipe] = useState(initial);
  const [saved, setSaved] = useState(initial);
  const [query, setQuery] = useState("");
  const [showSelected, setShowSelected] = useState(false);
  const [limit, setLimit] = useState(24);
  const [message, setMessage] = useState<{ text: string; error: boolean } | null>(null);
  const [busy, setBusy] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const problems = checkDependencies(recipe, themes, icons, mods);
  const dirty = JSON.stringify(recipe) !== JSON.stringify(saved);
  const visible = filterMods(mods, query).filter((mod) => !showSelected || recipe.windhawk.some((item) => item.id === mod.id));

  const update = (next: ThemeRecipe) => { setRecipe(next); setMessage(null); };
  const notifyError = (error: unknown) => {
    const key = error instanceof Error ? error.message : String(error);
    setMessage({ text: key === "invalid_parallax" ? tt("invalid_recipe") : ["invalid_recipe", "recipe_too_large"].includes(key) ? tt(key) : key, error: true });
  };
  const saveDraft = () => {
    try {
      const validated = parseRecipe(JSON.stringify(recipe));
      localStorage.setItem("theme-studio.recipe.v1", JSON.stringify(validated));
      setSaved(validated);
      setMessage({ text: tt("draft_saved"), error: false });
    } catch (error) { notifyError(error); }
  };
  const exportRecipe = async () => {
    try {
      const validated = parseRecipe(JSON.stringify(recipe));
      if (onExport) {
        const location = await onExport(validated);
        setMessage({ text: tt("exported_location", { path: location }), error: false });
        return;
      }
      const url = URL.createObjectURL(new Blob([JSON.stringify(validated, null, 2)], { type: "application/json" }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = (validated.name.replace(/[\\/:*?"<>|]/g, "_") || "theme") + ".theme.json";
      document.body.append(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
      setMessage({ text: tt("export_started"), error: false });
    } catch (error) { notifyError(error); }
  };
  const importRecipe = async (file?: File) => {
    if (!file) return;
    try {
      if (file.size > 1024 * 1024) throw new Error("recipe_too_large");
      const next = parseRecipe(await file.text());
      update(next);
      setMessage({ text: tt("imported"), error: false });
    } catch (error) { notifyError(error); }
    if (fileInput.current) fileInput.current.value = "";
  };
  const apply = async () => {
    if (!onApply || problems.length || busy) return;
    setBusy(true);
    try {
      const validated = parseRecipe(JSON.stringify(recipe));
      await onApply(validated);
      setMessage({ text: tt("seelen_applied"), error: false });
    } catch (error) { notifyError(error); }
    finally { setBusy(false); }
  };
  const resourceSwitch = (field: "activeThemes" | "activeIconPacks", id: string, checked: boolean) => {
    const items = recipe.seelen[field].filter((value) => value !== id);
    if (checked) items.push(id);
    update({ ...recipe, seelen: { ...recipe.seelen, [field]: items },
      ...(id === PARALLAX_THEME_ID ? { wallpaperParallax: { ...(recipe.wallpaperParallax || DEFAULT_PARALLAX), enabled: checked } } : {}) });
  };
  const parallax = recipe.wallpaperParallax || { ...DEFAULT_PARALLAX, enabled: recipe.seelen.activeThemes.includes(PARALLAX_THEME_ID) };
  const changeParallax = (wallpaperParallax: ParallaxSettings) => {
    const activeThemes = recipe.seelen.activeThemes.filter((id) => id !== PARALLAX_THEME_ID);
    if (wallpaperParallax.enabled) activeThemes.push(PARALLAX_THEME_ID);
    update({ ...recipe, wallpaperParallax, seelen: { ...recipe.seelen, activeThemes } });
  };

  return (
    <div className={cs.workbench}>
      {!embedded && <header className={cs.hero}>
        <div><p className={cs.eyebrow}>SEELEN UI · WINDHAWK</p><h1>{tt("title")}</h1><p>{tt("subtitle")}</p></div>
        <Tag color={native ? "green" : "blue"}>{tt(native ? "native_mode" : "preview_mode")}</Tag>
      </header>}
      {!native && !embedded && <Alert type="info" showIcon title={tt("preview_notice")} />}
      <div className={cs.topbar}>
        <input className={cs.textInput} aria-label={tt("name")} value={recipe.name} maxLength={120} onInput={(event) => update({ ...recipe, name: event.currentTarget.value })} />
        <Tag color={dirty ? "orange" : "default"}>{tt(dirty ? "unsaved" : "saved")}</Tag>
        <Button onClick={() => fileInput.current?.click()}>{tt("import")}</Button>
        <Button onClick={() => void exportRecipe()}>{tt("export")}</Button>
        <input ref={fileInput} type="file" accept=".json" hidden onChange={(event) => void importRecipe(event.currentTarget.files?.[0])} />
      </div>
      {message && <Alert type={message.error ? "error" : "success"} showIcon title={message.text} />}
      {!!problems.length && <Alert type="warning" showIcon title={tt("dependencies_missing")} description={problems.join(" · ")} />}
      {!embedded && <nav className={cs.anchors}>
        {["overview", ...(desktopClient ? ["desktop", "cursors"] : []), "parallax", "seelen", "windhawk"].map((id) => <a key={id} href={`#workbench-${id}`} onClick={(event) => {
          event.preventDefault(); document.getElementById(`workbench-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
        }}>{tt(id === "parallax" ? "parallax.title" : id === "desktop" ? "desktop_settings.icons_title" : id === "cursors" ? "desktop_settings.cursors_title" : id)}</a>)}
      </nav>}
      {!embedded && <section id="workbench-overview" className={groupStyles.group}>
        <div className={cs.sectionTitle}><h2>{tt("overview")}</h2><span>{tt("composition_notice")}</span></div>
        <div className={cs.overview}>
          <div className={cs.desktop} aria-label={tt("composition_notice")}>
            <div className={cs.toolbar}>◉ <span>{tt("desktop")}</span><span>▧ ◷</span></div>
            <div className={cs.previewCard}><span>◈</span><h3>{recipe.name || tt("name")}</h3><p>{tt("selection_counts", { themes: recipe.seelen.activeThemes.length, icons: recipe.seelen.activeIconPacks.length, mods: recipe.windhawk.length })}</p></div>
            <div className={cs.dock}><span>◧</span><span>◈</span><span>▣</span><span>✦</span><span>◉</span></div>
          </div>
          <div className={cs.summary}>
            <h3>{tt("current_selection")}</h3>
            <p>{tt("seelen_scope")}</p>
            <div className={cs.tags}>{recipe.seelen.activeThemes.map((id) => <Tag key={id} color="purple">{themes.find((item) => item.id === id)?.name || id}</Tag>)}</div>
            <div className={cs.tags}>{recipe.windhawk.map((mod) => <Tag key={mod.id}>{mods.find((item) => item.id === mod.id)?.name || mod.id}</Tag>)}</div>
            <p className={cs.muted}>{tt("windhawk_notice")}</p>
          </div>
        </div>
      </section>}
      {desktopClient && <DesktopPanel client={desktopClient} />}
      <ParallaxPanel settings={parallax} onChange={changeParallax} desktopClient={desktopClient} desktopNative={native} />
      <section id="workbench-seelen" className={groupStyles.group}>
        <div className={cs.sectionTitle}><h2>{tt("seelen")}</h2><span>{tt("seelen_description")}</span></div>
        <h3>{tt("themes")}</h3>
        <div className={cs.resourceGrid}>{themes.map((item) => <label key={item.id} className={cs.resourceCard}>
          <Checkbox disabled={item.id === "@default/theme"} checked={recipe.seelen.activeThemes.includes(item.id)} onChange={(event) => resourceSwitch("activeThemes", item.id, event.target.checked)} />
          <div><strong>{item.name}</strong><p>{item.description || item.id}</p></div>
        </label>)}</div>
        <h3>{tt("icon_packs")}</h3>
        <div className={cs.resourceGrid}>{icons.map((item) => <label key={item.id} className={cs.resourceCard}>
          <Checkbox disabled={item.id === "@system/icon-pack"} checked={recipe.seelen.activeIconPacks.includes(item.id)} onChange={(event) => resourceSwitch("activeIconPacks", item.id, event.target.checked)} />
          <div><strong>{item.name}</strong><p>{item.description || item.id}</p></div>
        </label>)}</div>
        {renderSettings}
        {renderRuntime?.(recipe)}
      </section>
      <section id="workbench-windhawk" className={groupStyles.group}>
        <div className={cs.sectionTitle}><h2>{tt("windhawk")}</h2><span>{tt("catalog_count", { count: mods.length })}</span></div>
        <Alert type="info" title={tt("windhawk_notice")} />
        <div className={cs.searchRow}>
          <input className={cs.textInput} type="search" aria-label={tt("search")} placeholder={tt("search")} value={query} onInput={(event) => { setQuery(event.currentTarget.value); setLimit(24); }} />
          <Checkbox checked={showSelected} onChange={(event) => { setShowSelected(event.target.checked); setLimit(24); }}>{tt("selected_only")}</Checkbox>
          <span>{visible.length}</span>
        </div>
        <div className={cs.modGrid}>{visible.slice(0, limit).map((mod) => {
          const selected = recipe.windhawk.find((item) => item.id === mod.id);
          if (renderMod) return <div key={mod.id}>{renderMod(mod, selected,
            (checked) => update(toggleMod(recipe, mod, checked)),
            (theme) => update({ ...recipe, windhawk: recipe.windhawk.map((item) => item.id === mod.id ? { ...item, settings: { ...item.settings, theme } } : item) }))}</div>;
          return <article key={mod.id} className={cs.modCard}>
            <div className={cs.modTitle}><h3>{mod.name}</h3><Checkbox aria-label={tt("select_mod", { name: mod.name })} checked={!!selected} onChange={(event) => update(toggleMod(recipe, mod, event.target.checked))} /></div>
            <p>{mod.description}</p>
            <div className={cs.tags}><Tag>{mod.version}</Tag><Tag>{mod.license}</Tag></div>
            {mod.include.length > 0 && <p className={cs.processes}>{mod.include.join(", ")}</p>}
            {!!mod.themeChoices.length && <Select aria-label={tt("preset", { name: mod.name })} placeholder={tt("choose_preset")} value={selected?.settings.theme as string | undefined} disabled={!selected} allowClear
              options={mod.themeChoices.map((choice) => ({ value: choice.id, label: choice.label }))}
              onChange={(theme: string | undefined) => update({ ...recipe, windhawk: recipe.windhawk.map((item) => {
                if (item.id !== mod.id) return item;
                const settings = { ...item.settings };
                if (theme === undefined) delete settings.theme; else settings.theme = theme;
                return { ...item, settings };
              }) })} />}
            <a href={mod.source} target="_blank" rel="noopener noreferrer">{tt("view_source")}</a>
          </article>;
        })}</div>
        {!visible.length && <p>{tt("no_results")}</p>}
        {visible.length > limit && <Button onClick={() => setLimit(limit + 24)}>{tt("load_more")}</Button>}
      </section>
      <footer className={cs.footer}>
        <span>{tt("selected_count", { count: recipe.windhawk.length })}</span>
        <Button disabled={!dirty || busy} onClick={() => { setRecipe(saved); setMessage(null); }}>{tt("restore_draft")}</Button>
        <Button onClick={saveDraft} disabled={busy}>{tt("save_draft")}</Button>
        {onApply && <Button type="primary" disabled={!native || !!problems.length || busy} loading={busy} onClick={() => void apply()}>{tt("apply_seelen")}</Button>}
      </footer>
    </div>
  );
}
