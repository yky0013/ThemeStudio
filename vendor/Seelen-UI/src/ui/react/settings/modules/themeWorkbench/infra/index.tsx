// SPDX-License-Identifier: AGPL-3.0-or-later
import { useMemo } from "preact/hooks";
import { invoke, SeelenCommand } from "@seelen-ui/lib";
import { getResourceText } from "libs/ui/react/utils/index.ts";
import yaml from "js-yaml";
import { useTranslation } from "react-i18next";
import i18n from "../../../i18n/index.ts";
import en from "../../../i18n/translations/workbench.en.yml";
import zh from "../../../i18n/translations/workbench.zh-CN.yml";
import { settings, hasChanges } from "../../../state/mod.ts";
import { themes, iconPacks, widgets } from "../../../state/resources.ts";
import { WidgetConfiguration } from "../../resources/Widget/View.tsx";
import { WorkbenchView } from "./View.tsx";
import catalog from "../domain/catalog.json";
import { checkDependencies, parseRecipe } from "../domain/model.ts";
import type { ThemeRecipe } from "../domain/model.ts";
import policy from "../../../../../../../../../config/feature-policy.json";
import { adoptedSeelenComponents } from "../domain/adoption.ts";
import type { ProviderPolicy } from "../domain/adoption.ts";
import { fromThemeVariables, PARALLAX_THEME_ID, toThemeVariables } from "../../../../../../../libs/ui/shared/wallpaper-parallax/motion.ts";

i18n.addResourceBundle("en", "translation", yaml.load(en), true, true);
i18n.addResourceBundle("zh-CN", "translation", yaml.load(zh), true, true);

export function ThemeWorkbench() {
  const { t } = useTranslation();
  const themeChoices = themes.value.map((item) => ({ id: item.id, name: getResourceText(item.metadata.displayName, i18n.language) }));
  const iconChoices = iconPacks.value.map((item) => ({ id: item.id, name: getResourceText(item.metadata.displayName, i18n.language) }));
  const initial = useMemo<ThemeRecipe>(() => {
    const saved = localStorage.getItem("theme-workbench.recipe.v1");
    if (saved) {
      try { return parseRecipe(saved); } catch (error) { console.warn("Unable to read saved workbench recipe", error); }
    }
    return {
      schemaVersion: 1, name: t("theme_workbench.title"),
      seelen: { activeThemes: [...settings.value.activeThemes], activeIconPacks: [...settings.value.activeIconPacks] },
      windhawk: [],
      wallpaperParallax: fromThemeVariables(settings.value.activeThemes.includes(PARALLAX_THEME_ID), settings.value.byTheme[PARALLAX_THEME_ID]),
    };
  }, []);

  const apply = async (recipe: ThemeRecipe) => {
    if (hasChanges.value) throw new Error(t("theme_workbench.pending_changes"));
    if (checkDependencies(recipe, themeChoices, iconChoices, catalog.mods).length) {
      throw new Error(t("theme_workbench.dependencies_missing"));
    }
    // All unrelated Seelen settings are retained. Windhawk is intentionally not
    // invoked here: native mod execution requires the separate Windhawk host.
    const current = await invoke(SeelenCommand.StateGetSettings, { path: null });
    if (hasChanges.value) throw new Error(t("theme_workbench.pending_changes"));
    const next = {
      ...current,
      activeThemes: ["@default/theme", ...recipe.seelen.activeThemes.filter((id) => id !== "@default/theme")],
      activeIconPacks: ["@system/icon-pack", ...recipe.seelen.activeIconPacks.filter((id) => id !== "@system/icon-pack")],
      byTheme: recipe.wallpaperParallax ? { ...current.byTheme, [PARALLAX_THEME_ID]: toThemeVariables(recipe.wallpaperParallax) } : current.byTheme,
    };
    await invoke(SeelenCommand.StateWriteSettings, { settings: next });
    settings.value = next;
  };
  // Overlapping native components stay unbound until the user picks a provider.
  const componentIds = adoptedSeelenComponents(policy as ProviderPolicy);
  return <WorkbenchView mods={catalog.mods} themes={themeChoices} icons={iconChoices} initial={initial} native onApply={apply}
    renderSettings={<>
      <h3>{t("theme_workbench.widget_settings")}</h3>
      <p>{t("theme_workbench.widget_description")}</p>
      {componentIds.filter((id) => widgets.value.some((item) => item.id === id)).map((id) =>
        <details key={id}><summary>{getResourceText(widgets.value.find((item) => item.id === id)!.metadata.displayName, i18n.language)}</summary><WidgetConfiguration widgetId={id} /></details>
      )}
    </>} />;
}
