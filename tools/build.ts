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
const mods = fs.readdirSync(modRoot).filter((file) => file.endsWith(".wh.cpp")).sort().map((file) => {
  const source = fs.readFileSync(path.join(modRoot, file), "utf8");
  const metadata = parser.extractMetadata(source, "zh-CN");
  const block = source.match(/\/\/ ==WindhawkModSettings==\s*\/\*([\s\S]*?)\*\/\s*\/\/ ==\/WindhawkModSettings==/);
  const declarations = block ? yaml.load(block[1]!) as Record<string, unknown>[] : [];
  const options = Array.isArray(declarations) ? declarations.find((item) => Object.hasOwn(item, "theme"))?.$options : undefined;
  const themeChoices = Array.isArray(options) ? options.flatMap((item) => typeof item === "object" && item ? Object.entries(item).map(([id, label]) => ({ id, label: String(label) })) : []) : [];
  return { id: metadata.id!, name: metadata.name || metadata.id!, description: metadata.description || "", author: metadata.author || "", version: metadata.version || "", include: metadata.include || [], architecture: metadata.architecture || [], license: metadata.license || (/Source code is published under The GNU General Public License v3\.0\./.test(source) ? "GPL-3.0" : "MIT (repository default)"), source: `https://github.com/ramensoftware/windhawk-mods/blob/${provenance.Commit}/mods/${file}`, sha256: createHash("sha256").update(source).digest("hex"), themeChoices };
});
fs.writeFileSync(path.join(project, "vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/catalog.json"), JSON.stringify({ sourceCommit: provenance.Commit, mods }, null, 2) + "\n");
await esbuild.build({ absWorkingDir: project, entryPoints: { app: "src/app/main.tsx" }, bundle: true, minify: true,
  format: "esm", platform: "browser", target: "es2022", outdir: "dist", metafile: true,
  jsx: "automatic", jsxImportSource: "preact", loader: { ".yml": "text" }, nodePaths: [modules],
  alias: { react: path.join(modules, "preact/compat"), "react-dom": path.join(modules, "preact/compat"), "react/jsx-runtime": path.join(modules, "preact/jsx-runtime") },
  plugins: [sveltePlugin({ compilerOptions: { css: "injected", dev: false } }), cssModules({ localsConvention: "camelCase", pattern: "studio-[local]-[hash]", targets: {} })],
}).then((result) => {
  fs.mkdirSync(path.join(project, "build"), { recursive: true });
  fs.writeFileSync(path.join(project, "build/bundle-inputs.json"), JSON.stringify(result.metafile, null, 2));
});
fs.copyFileSync(path.join(project, "src/app/index.html"), path.join(project, "dist/index.html"));
fs.cpSync(path.join(project, "vendor/Seelen-UI/src/ui/react/settings/public/fixtures"), path.join(project, "dist/fixtures"), { recursive: true });
fs.cpSync(path.join(project, "licenses"), path.join(project, "dist/licenses"), { recursive: true });
console.log(`Theme Studio built with Seelen navigation/media and Windhawk card components; ${mods.length} source-backed mods.`);
