// SPDX-License-Identifier: AGPL-3.0-or-later
// Theme composition model. A Windhawk selection is a draft, never an installed mod.
import { PARALLAX_THEME_ID, parseParallax } from "../../../../../../../libs/ui/shared/wallpaper-parallax/motion.ts";
import type { ParallaxSettings } from "../../../../../../../libs/ui/shared/wallpaper-parallax/motion.ts";
export type SettingValue = string | number | boolean;
export interface ModChoice {
  id: string;
  label: string;
}
export interface ModResource {
  id: string;
  name: string;
  description: string;
  author: string;
  version: string;
  license: string;
  include: string[];
  architecture: string[];
  source: string;
  sha256: string;
  themeChoices: ModChoice[];
}
export interface ModDraft {
  id: string;
  sourceHash: string;
  settings: Record<string, SettingValue>;
}
export interface ThemeRecipe {
  schemaVersion: 1;
  name: string;
  seelen: {
    activeThemes: string[];
    activeIconPacks: string[];
  };
  windhawk: ModDraft[];
  wallpaperParallax?: ParallaxSettings;
}
export interface ResourceChoice {
  id: string;
  name: string;
  description?: string;
}

function record(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
function ids(value: unknown): value is string[] {
  return Array.isArray(value) && value.length <= 100 &&
    value.every((id) => typeof id === "string" && id.length > 0 && id.length <= 256) &&
    new Set(value).size === value.length;
}

export function parseRecipe(text: string): ThemeRecipe {
  if (text.length > 1024 * 1024) throw new Error("recipe_too_large");
  const data: unknown = JSON.parse(text);
  if (!record(data) || data.schemaVersion !== 1 || typeof data.name !== "string" ||
    !data.name.trim() || data.name.length > 120 || !record(data.seelen) ||
    !ids(data.seelen.activeThemes) || !ids(data.seelen.activeIconPacks) ||
    !Array.isArray(data.windhawk) || data.windhawk.length > 100) {
    throw new Error("invalid_recipe");
  }
  const seen = new Set<string>();
  const windhawk: ModDraft[] = data.windhawk.map((item: unknown) => {
    if (!record(item) || typeof item.id !== "string" || !/^[a-z0-9-]+$/.test(item.id) ||
      seen.has(item.id) || typeof item.sourceHash !== "string" ||
      !/^[a-f0-9]{64}$/.test(item.sourceHash) || !record(item.settings) ||
      Object.keys(item.settings).length > 200) throw new Error("invalid_recipe");
    seen.add(item.id);
    const settings: Record<string, SettingValue> = Object.create(null);
    for (const [key, value] of Object.entries(item.settings)) {
      if (!key || key.length > 100 || ["__proto__", "constructor", "prototype"].includes(key) ||
        !["string", "number", "boolean"].includes(typeof value) ||
        (typeof value === "number" && !Number.isFinite(value)) ||
        (typeof value === "string" && value.length > 8192)) throw new Error("invalid_recipe");
      settings[key] = value as SettingValue;
    }
    return { id: item.id, sourceHash: item.sourceHash, settings };
  });
  const wallpaperParallax = data.wallpaperParallax === undefined ? undefined : parseParallax(data.wallpaperParallax);
  if (wallpaperParallax && wallpaperParallax.enabled !== data.seelen.activeThemes.includes(PARALLAX_THEME_ID)) throw new Error("invalid_recipe");
  return {
    schemaVersion: 1,
    name: data.name.trim(),
    seelen: {
      activeThemes: [...data.seelen.activeThemes],
      activeIconPacks: [...data.seelen.activeIconPacks],
    },
    windhawk,
    ...(wallpaperParallax ? { wallpaperParallax } : {}),
  };
}

export function checkDependencies(
  recipe: ThemeRecipe,
  themes: ResourceChoice[],
  icons: ResourceChoice[],
  mods: ModResource[],
): string[] {
  const problems: string[] = [];
  if (recipe.wallpaperParallax?.enabled && recipe.windhawk.some((mod) => mod.id === "parallax-wallpaper")) problems.push("conflict:parallax-wallpaper");
  for (const id of recipe.seelen.activeThemes) {
    if (!themes.some((item) => item.id === id)) problems.push(`theme:${id}`);
  }
  for (const id of recipe.seelen.activeIconPacks) {
    if (!icons.some((item) => item.id === id)) problems.push(`icon:${id}`);
  }
  for (const selected of recipe.windhawk) {
    const mod = mods.find((item) => item.id === selected.id);
    if (!mod) problems.push(`mod:${selected.id}`);
    else {
      if (mod.sha256 !== selected.sourceHash) problems.push(`source:${selected.id}`);
      const theme = selected.settings.theme;
      if (theme !== undefined && !mod.themeChoices.some((choice) => choice.id === theme)) {
        problems.push(`preset:${selected.id}`);
      }
    }
  }
  return problems;
}

export function toggleMod(recipe: ThemeRecipe, mod: ModResource, selected: boolean): ThemeRecipe {
  const next = recipe.windhawk.filter((item) => item.id !== mod.id);
  if (selected) next.push({ id: mod.id, sourceHash: mod.sha256, settings: {} });
  return { ...recipe, windhawk: next };
}

export function filterMods(mods: ModResource[], query: string): ModResource[] {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return mods.filter((mod) => words.every((word) =>
    [mod.id, mod.name, mod.description, mod.author, ...mod.include].join(" ").toLocaleLowerCase().includes(word)
  ));
}
