import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import esbuild from "esbuild";
import cssModules from "esbuild-css-modules-plugin";
import sveltePlugin from "esbuild-svelte";
import { createRequire } from "node:module";
const { compile, compileModule } = createRequire(import.meta.url)("svelte/compiler");

const directory = path.dirname(fileURLToPath(import.meta.url));
const modules = path.join(directory, "node_modules");
fs.mkdirSync(path.join(directory, "dist"), { recursive: true });
await esbuild.build({
  absWorkingDir: directory, entryPoints: ["preview.tsx"], bundle: true, minify: true,
  format: "esm", platform: "browser", target: "es2022", outdir: "dist",
  jsx: "automatic", jsxImportSource: "preact", loader: { ".yml": "text" },
  nodePaths: [modules],
  alias: {
    react: path.join(modules, "preact/compat"),
    "react-dom": path.join(modules, "preact/compat"),
    "react/jsx-runtime": path.join(modules, "preact/jsx-runtime"),
  },
  plugins: [sveltePlugin({ compilerOptions: { css: "injected", dev: false } }), cssModules({ localsConvention: "camelCase", pattern: "workbench-[local]-[hash]", targets: {} })],
});
fs.cpSync(path.join(directory, "../../src/ui/react/settings/public/fixtures"), path.join(directory, "dist/fixtures"), { recursive: true });
fs.copyFileSync(path.join(directory, "index.html"), path.join(directory, "dist/index.html"));
fs.copyFileSync(path.join(directory, "../../LICENSE"), path.join(directory, "dist/LICENSE"));
fs.copyFileSync(path.join(directory, "../../documentation/licenses/windhawk-parallax-MIT.txt"), path.join(directory, "dist/windhawk-parallax-MIT.txt"));
fs.copyFileSync(path.join(directory, "../../../icon-workbench/licenses/Cursor-Palette.txt"), path.join(directory, "dist/Cursor-Palette-MIT.txt"));
fs.writeFileSync(path.join(directory, "dist/NOTICE.txt"), "Seelen UI source-based development preview. Original Seelen authors and AGPL license retained.\nSeelen image/video components are reused with an additional transform layer. Motion, spring and projective geometry algorithms are adapted from HaVeN80's Parallax Wallpaper 0.9.0 (MIT); see windhawk-parallax-MIT.txt and documentation/wallpaper-parallax.md. The standalone Windhawk wallpaper renderer is not started.\nDesktop shortcut and system cursor actions call the existing local icon-workbench/backend.py and cursor_adapter.py through desktop_bridge.py; ordinary images use image-to-ico/converter.py. Cursor Palette attribution and MIT terms are in Cursor-Palette-MIT.txt.\nFull modified source includes libs/ui/shared/wallpaper-parallax, libs/ui/svelte/components/Wallpaper, src/ui/react/settings/modules/themeWorkbench and tools/theme-workbench.\nFrontend dependencies retain their package licenses in ../node_modules.\n");
// Parse the native route adapter as well. This is a syntax check, not a native
// compilation or a substitute for the missing Rust-generated Seelen bindings.
await esbuild.transform(fs.readFileSync(path.join(directory, "../../src/ui/react/settings/modules/themeWorkbench/infra/index.tsx"), "utf8"), { loader: "tsx", jsx: "automatic" });
const monitorPath = path.join(directory, "../../src/ui/svelte/wallpaper-manager/modules/Monitor/Monitor.svelte");
compile(fs.readFileSync(monitorPath, "utf8"), { filename: monitorPath, generate: "client", dev: false });
const statePath = path.join(directory, "../../src/ui/svelte/wallpaper-manager/state.svelte.ts");
const stateJs = await esbuild.transform(fs.readFileSync(statePath, "utf8"), { loader: "ts", target: "esnext" });
compileModule(stateJs.code, { filename: statePath.replace(/\.ts$/, ".js"), generate: "client", dev: false });
console.log("Built shared Seelen media components with parallax; compiled the native Svelte monitor adapter.");
