import assert from "node:assert/strict";
import { test } from "node:test";
import { acceptInput, advance, coversViewport, createMotion, DEFAULT_PARALLAX, fromThemeVariables, normalized, PARALLAX_THEME_ID, parseParallax, perspectiveZoom, PRESETS, resolveOptions, springAxis, tiltCoefficients, toThemeVariables, transformMatrix } from "../vendor/Seelen-UI/libs/ui/shared/wallpaper-parallax/motion.ts";
import { checkDependencies, parseRecipe } from "../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/model.ts";
import type { ParallaxSettings } from "../vendor/Seelen-UI/libs/ui/shared/wallpaper-parallax/motion.ts";

test("upstream spring reaches approximately 95% at its configured settling time", () => {
  const axis = { position: 0, velocity: 0 };
  springAxis(axis, 1, 4.744 / .750, .750, 1);
  assert.ok(Math.abs(axis.position - .95) < .0001);
});
test("spring result is frame-rate independent for a constant target", () => {
  const run = (fps: number) => {
    const s = createMotion(), options = resolveOptions({ ...DEFAULT_PARALLAX, enabled: true });
    acceptInput(s, .9, -.7, options.threshold);
    for (let i = 0; i < fps; i++) advance(s, options, 1000 / fps);
    return s;
  };
  const a = run(30), b = run(144);
  assert.ok(Math.abs(a.x.position - b.x.position) < 1e-10);
  assert.ok(Math.abs(a.tiltY.position - b.tiltY.position) < 1e-10);
});
test("long stalls are clamped and pointer dead zone filters small movement", () => {
  const s = createMotion(), options = resolveOptions(DEFAULT_PARALLAX);
  acceptInput(s, .01, .01, options.threshold);
  assert.equal(s.acceptedX, 0);
  acceptInput(s, 1, 0, options.threshold);
  const short = structuredClone(s);
  advance(s, options, 60000); advance(short, options, 50);
  assert.deepEqual(s, short);
  assert.ok(s.x.position < options.x / 2);
});
test("global pointer normalization handles negative monitor origins and independent displays", () => {
  const left = { left: -1920, right: 0, top: 200, bottom: 1280 };
  assert.deepEqual(normalized(left, -960, 740), [0, 0]);
  assert.equal(normalized(left, 10, 500), null);
  assert.equal(normalized({ left: 0, right: 0, top: 0, bottom: 0 }, 0, 0), null);
});
test("constant auto-zoom covers viewport corners over all presets, sizes and tilt samples", () => {
  for (const preset of Object.keys(PRESETS) as ParallaxSettings["preset"][]) {
    for (const [width, height] of [[640, 360], [3840, 2160], [1920, 1080], [600, 1000], [3440, 1440]]) {
      const options = resolveOptions({ ...DEFAULT_PARALLAX, enabled: true, preset, tilt: 8 });
      const zoom = perspectiveZoom(width!, height!, options);
      assert.ok(zoom >= 1 && zoom < 2);
      for (let x = -1; x <= 1; x += .2) for (let y = -1; y <= 1; y += .2) {
        assert.ok(coversViewport(width!, height!, tiltCoefficients(width!, height!, 8, x, y), zoom + .00001));
      }
    }
  }
});
test("matrix maps padded source center to viewport center and preserves finite homogeneous coordinates", () => {
  const s = createMotion(), options = resolveOptions({ ...DEFAULT_PARALLAX, enabled: true, tilt: 8, strength: 2 });
  acceptInput(s, 1, -.8, options.threshold);
  for (let i = 0; i < 100; i++) advance(s, options, 16);
  const width = 1920, height = 1080;
  const m = transformMatrix(width, height, s, options, perspectiveZoom(width, height, options));
  const sx = width / 2 + options.x + s.x.position, sy = height / 2 + options.y + s.y.position;
  const w = sx * m[3]! + sy * m[7]! + m[15]!;
  assert.ok(Math.abs((sx * m[0]! + sy * m[4]! + m[12]!) / w - width / 2) < 1e-8);
  assert.ok(Math.abs((sx * m[1]! + sy * m[5]! + m[13]!) / w - height / 2) < 1e-8);
  assert.ok(m.every(Number.isFinite));
});
test("source theme values round-trip with strict user configuration validation", () => {
  const p = { ...DEFAULT_PARALLAX, enabled: true, preset: "cinema" as const, strength: 1.8, tilt: 6 };
  assert.deepEqual(fromThemeVariables(true, toThemeVariables(p)), p);
  assert.throws(() => parseParallax({ ...p, strength: 100 }));
  assert.throws(() => parseParallax({ ...p, preset: "__proto__" }));
  assert.throws(() => parseParallax({ ...p, tilt: NaN }));
});
test("recipe persists the combination and rejects contradictory enablement", () => {
  const recipe = { schemaVersion: 1, name: "视频视差", seelen: { activeThemes: ["@default/theme", PARALLAX_THEME_ID], activeIconPacks: [] }, windhawk: [], wallpaperParallax: { ...DEFAULT_PARALLAX, enabled: true } };
  assert.deepEqual(parseRecipe(JSON.stringify(recipe)), recipe);
  assert.throws(() => parseRecipe(JSON.stringify({ ...recipe, wallpaperParallax: DEFAULT_PARALLAX })));
  const conflicting = parseRecipe(JSON.stringify({ ...recipe, windhawk: [{ id: "parallax-wallpaper", sourceHash: "a".repeat(64), settings: {} }] }));
  assert.ok(checkDependencies(conflicting, [], [], []).includes("conflict:parallax-wallpaper"));
});
