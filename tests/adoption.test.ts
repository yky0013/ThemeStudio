import assert from "node:assert/strict";
import { test } from "node:test";
import { adoptedSeelenComponents } from "../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/adoption.ts";
import type { ProviderPolicy } from "../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/adoption.ts";

test("an unresolved overlap cannot silently bind a Seelen component", () => {
  const pending: ProviderPolicy = { decisions: { wallpaper: { status: "awaiting_user", provider: "seelen" }, taskbar: { status: "awaiting_user", provider: "seelen" } } };
  assert.deepEqual(adoptedSeelenComponents(pending), []);
});
test("the user's split wallpaper choice binds Seelen wallpaper without choosing a taskbar", () => {
  const split: ProviderPolicy = { decisions: { wallpaper: { status: "chosen_by_user", provider: "both" }, taskbar: { status: "awaiting_user", provider: null } } };
  assert.deepEqual(adoptedSeelenComponents(split), ["@seelen/wallpaper-manager"]);
});
