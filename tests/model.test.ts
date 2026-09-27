import assert from "node:assert/strict";
import { test } from "node:test";
import { checkDependencies, filterMods, parseRecipe, toggleMod } from "../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/model.ts";
import type { ModResource, ThemeRecipe } from "../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/model.ts";
import catalog from "../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/catalog.json";

const first = catalog.mods.find((item) => item.id === "windows-11-taskbar-styler")!;
const recipe: ThemeRecipe = { schemaVersion: 1, name: "我的桌面", seelen: { activeThemes: ["@default/theme"], activeIconPacks: ["@system/icon-pack"] }, windhawk: [] };
test("configuration round trip keeps Unicode names and mod version identity", () => {
  const selected = toggleMod(recipe, first, true);
  assert.deepEqual(JSON.parse(JSON.stringify(parseRecipe(JSON.stringify(selected)))), selected);
  assert.equal(selected.windhawk[0]?.sourceHash, first.sha256);
});
test("adding or removing a mod never mutates the input and never adds duplicates", () => {
  const selected = toggleMod(recipe, first, true);
  assert.equal(recipe.windhawk.length, 0);
  assert.equal(toggleMod(selected, first, true).windhawk.length, 1);
  assert.equal(toggleMod(selected, first, false).windhawk.length, 0);
});
test("import rejects invalid versions, duplicates and prototype keys", () => {
  assert.throws(() => parseRecipe(JSON.stringify({ ...recipe, schemaVersion: 2 })));
  assert.throws(() => parseRecipe(JSON.stringify({ ...recipe, seelen: { ...recipe.seelen, activeThemes: ["a", "a"] } })));
  const item = { id: first.id, sourceHash: first.sha256, settings: {} };
  assert.throws(() => parseRecipe(JSON.stringify({ ...recipe, windhawk: [item, item] })));
  assert.throws(() => parseRecipe(JSON.stringify({ ...recipe, windhawk: [{ ...item, settings: JSON.parse('{"__proto__":"bad"}') }] })));
});
test("oversized and malformed input do not replace the input recipe", () => {
  assert.throws(() => parseRecipe(" ".repeat(1024 * 1024 + 1)), /recipe_too_large/);
  assert.throws(() => parseRecipe("not json"));
  assert.equal(recipe.name, "我的桌面");
});
test("missing resources and changed mod source are reported before application", () => {
  const selected = toggleMod(recipe, first, true);
  const themes = [{ id: "@default/theme", name: "Default" }];
  const icons = [{ id: "@system/icon-pack", name: "System" }];
  assert.deepEqual(checkDependencies(selected, themes, icons, catalog.mods), []);
  const changed = { ...first, sha256: "0".repeat(64) };
  assert.ok(checkDependencies(selected, themes, icons, [changed]).includes(`source:${first.id}`));
  assert.ok(checkDependencies(selected, [], [], []).includes(`mod:${first.id}`));
});
test("unknown preset fails validation", () => {
  const selected = toggleMod(recipe, first, true);
  selected.windhawk[0]!.settings.theme = "not-a-real-preset";
  assert.ok(checkDependencies(selected, [{ id: "@default/theme", name: "" }], [{ id: "@system/icon-pack", name: "" }], catalog.mods).includes(`preset:${first.id}`));
});
test("catalog search includes localized names and target process", () => {
  const result = filterMods(catalog.mods, "explorer.exe taskbar");
  assert.ok(result.some((item) => item.id === first.id));
  assert.equal(filterMods(catalog.mods, "unfindableterm889944").length, 0);
});
test("catalog has unique ids, real source hashes and all three style modules", () => {
  assert.equal(new Set(catalog.mods.map((mod) => mod.id)).size, catalog.mods.length);
  assert.ok(catalog.mods.length > 500);
  for (const id of ["windows-11-taskbar-styler", "windows-11-start-menu-styler", "windows-11-file-explorer-styler"]) {
    const mod = catalog.mods.find((item) => item.id === id)!;
    assert.match(mod.sha256, /^[a-f0-9]{64}$/);
    assert.ok(mod.themeChoices.length > 5);
    assert.equal(mod.license, "GPL-3.0");
  }
});
