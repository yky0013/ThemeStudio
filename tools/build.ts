// SPDX-License-Identifier: AGPL-3.0-or-later
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import esbuild from "esbuild";
import cssModules from "esbuild-css-modules-plugin";
import sveltePlugin from "esbuild-svelte";
import { createHash } from "node:crypto";
import yaml from "js-yaml";
import ModSourceUtils from "../vendor/windhawk-mods/modSourceUtils.ts";

const project = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const modules = path.join(project, "node_modules");
const modRoot = path.join(project, "vendor/windhawk-mods/mods");
const parser = new ModSourceUtils(modRoot);
const provenance = JSON.parse(fs.readFileSync(path.join(project, "vendor/upstream-snapshots/windhawk-mods-source.json"), "utf8").replace(/^\uFEFF/, ""));
const modFiles = fs.readdirSync(modRoot).filter((file) => file.endsWith(".wh.cpp")).sort().map(file => ({file, root: modRoot, local: false}));
modFiles.push({file: 'themestudio-explorer-background.wh.cpp', root: path.join(project, 'components/explorer-skin'), local: true});
const mods = modFiles.map(({file, root, local}) => {
  const source = fs.readFileSync(path.join(root, file), "utf8").replace(/\r\n/g, "\n");
  const metadata = parser.extractMetadata(source, "zh-CN");
  const block = source.match(/\/\/ ==WindhawkModSettings==\s*\/\*([\s\S]*?)\*\/\s*\/\/ ==\/WindhawkModSettings==/);
  const declarations = block ? yaml.load(block[1]!) as Record<string, unknown>[] : [];
  const options = Array.isArray(declarations) ? declarations.find((item) => Object.hasOwn(item, "theme"))?.$options : undefined;
  const themeChoices = Array.isArray(options) ? options.flatMap((item) => typeof item === "object" && item ? Object.entries(item).map(([id, label]) => ({ id, label: String(label) })) : []) : [];
  return { id: metadata.id!, name: metadata.name || metadata.id!, description: metadata.description || "", author: metadata.author || "", version: metadata.version || "", include: metadata.include || [], architecture: metadata.architecture || [], license: metadata.license || (/Source code is published under The GNU General Public License v3\.0\./.test(source) ? "GPL-3.0" : "MIT (repository default)"), source: local ? 'https://github.com/yky0013/ThemeStudio' : `https://github.com/ramensoftware/windhawk-mods/blob/${provenance.Commit}/mods/${file}`, sourceKind: local ? 'themestudio' : 'upstream', sha256: createHash("sha256").update(source).digest("hex"), themeChoices };
});
fs.writeFileSync(path.join(project, "vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/catalog.json"), JSON.stringify({ sourceCommit: provenance.Commit, mods }, null, 2) + "\n");
await esbuild.build({ absWorkingDir: project, entryPoints: { app: "src/app/main.tsx", wallpaper: "src/app/wallpaper.ts" }, bundle: true, minify: true,
  format: "esm", platform: "browser", target: "es2022", outdir: "dist", metafile: true,
  jsx: "automatic", jsxImportSource: "preact", loader: { ".yml": "text" }, nodePaths: [modules],
  alias: { react: path.join(modules, "preact/compat"), "react-dom": path.join(modules, "preact/compat"), "react/jsx-runtime": path.join(modules, "preact/jsx-runtime") },
  plugins: [sveltePlugin({ compilerOptions: { css: "injected", dev: false } }), cssModules({ localsConvention: "camelCase", pattern: "studio-[local]-[hash]", targets: {} })],
}).then((result) => {
  fs.mkdirSync(path.join(project, "build"), { recursive: true });
  fs.writeFileSync(path.join(project, "build/bundle-inputs.json"), JSON.stringify(result.metafile, null, 2));
});
fs.copyFileSync(path.join(project, "src/app/index.html"), path.join(project, "dist/index.html"));
fs.copyFileSync(path.join(project, "src/app/wallpaper.html"), path.join(project, "dist/wallpaper.html"));
// Only catalogued packs are shipping assets; archived artwork stays out of builds.
const templateRoot = path.join(project, "assets/templates");
const templateCatalog = JSON.parse(fs.readFileSync(path.join(templateRoot, "catalog.json"), "utf8"));
fs.mkdirSync(path.join(project, "dist/templates"), { recursive: true });
fs.copyFileSync(path.join(templateRoot, "catalog.json"), path.join(project, "dist/templates/catalog.json"));
for (const pack of templateCatalog) fs.cpSync(path.join(templateRoot, pack.id), path.join(project, "dist/templates", pack.id), { recursive: true });
fs.cpSync(path.join(project, "assets/brand"), path.join(project, "dist/brand"), { recursive: true });
fs.cpSync(path.join(project, "vendor/Seelen-UI/src/ui/react/settings/public/fixtures"), path.join(project, "dist/fixtures"), { recursive: true });
fs.cpSync(path.join(project, "licenses"), path.join(project, "dist/licenses"), { recursive: true });
if (fs.existsSync(path.join(project, "docs/guide"))) fs.cpSync(path.join(project, "docs/guide"), path.join(project, "dist/help"), { recursive: true });
console.log(`Theme Studio built with Seelen navigation/media and Windhawk card components; ${mods.length} source-backed mods.`);
