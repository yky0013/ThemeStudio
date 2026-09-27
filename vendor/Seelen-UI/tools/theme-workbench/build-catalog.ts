// Imports the actual Windhawk repository parser; mod C++ is read, never executed.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import yaml from "js-yaml";
import ModSourceUtils from "../../../windhawk-mods/modSourceUtils.ts";

const project = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const root = path.resolve(project, "..");
const modRoot = path.join(root, "windhawk-mods/mods");
const parser = new ModSourceUtils(modRoot);
const provenance = JSON.parse(fs.readFileSync(path.join(root, "upstream-snapshots/windhawk-mods-source.json"), "utf8").replace(/^\uFEFF/, ""));
const mods = [];
const errors: { path: string; message: string }[] = [];
for (const file of fs.readdirSync(modRoot).filter((file) => file.endsWith(".wh.cpp")).sort()) {
  try {
    const source = fs.readFileSync(path.join(modRoot, file), "utf8");
    const metadata = parser.extractMetadata(source, "zh-CN");
    if (metadata.id + ".wh.cpp" !== file) throw new Error("Source id does not match file name");
    const block = source.match(/\/\/ ==WindhawkModSettings==\s*\/\*([\s\S]*?)\*\/\s*\/\/ ==\/WindhawkModSettings==/);
    const declarations = block ? yaml.load(block[1]!) as Record<string, unknown>[] : [];
    const themeDeclaration = Array.isArray(declarations) ? declarations.find((item) => Object.hasOwn(item, "theme")) : undefined;
    const options = themeDeclaration?.$options;
    const themeChoices = Array.isArray(options) ? options.flatMap((item) =>
      typeof item === "object" && item ? Object.entries(item).map(([id, label]) => ({ id, label: String(label) })) : []
    ) : [];
    const explicitLicense = source.match(/Source code is published under The GNU General Public License v3\.0\./);
    mods.push({
      id: metadata.id!, name: metadata.name || metadata.id!, description: metadata.description || "",
      author: metadata.author || "", version: metadata.version || "", include: metadata.include || [],
      architecture: metadata.architecture || [], license: metadata.license || (explicitLicense ? "GPL-3.0" : "MIT (repository default)"),
      source: `https://github.com/ramensoftware/windhawk-mods/blob/${provenance.Commit}/mods/${file}`,
      sha256: createHash("sha256").update(source).digest("hex"), themeChoices,
    });
  } catch (error) {
    errors.push({ path: file, message: String(error) });
  }
}
if (!mods.length || errors.length) throw new Error(`Catalog contains failures: ${JSON.stringify(errors)}`);
const directory = path.join(project, "src/ui/react/settings/modules/themeWorkbench/domain");
fs.writeFileSync(path.join(directory, "catalog.json"), JSON.stringify({ sourceCommit: provenance.Commit, mods }, null, 2) + "\n");
console.log(`Generated ${mods.length} mods from ${provenance.Commit}; no mod code executed.`);
