// SPDX-License-Identifier: AGPL-3.0-or-later
import { useEffect, useRef, useState } from "preact/hooks";
import { useTranslation } from "react-i18next";
import type { Artwork, ChangeResult, CursorImport, CursorScheme, DesktopClient, DesktopState } from "../domain/desktop.ts";
import { uploadFile } from "../domain/desktop.ts";
import groupStyles from "../../../components/SettingsBox/index.module.css";
import cs from "./desktop.module.css";

export function DesktopPanel({ client }: { client: DesktopClient }) {
  const { t } = useTranslation();
  const tt = (key: string, options?: Record<string, unknown>) => t(`theme_workbench.desktop_settings.${key}`, options);
  const [state, setState] = useState<DesktopState | null>(null);
  const [busy, setBusy] = useState(false);
  const running = useRef(false);
  const [message, setMessage] = useState<{ text: string; error: boolean } | null>(null);
  const [messageFor, setMessageFor] = useState<"icons" | "cursors">("icons");
  const [selected, setSelected] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [artwork, setArtwork] = useState<Artwork | null>(null);
  const [scheme, setScheme] = useState("");
  const [roles, setRoles] = useState<Record<string, string>>({});
  const [size, setSize] = useState(32);
  const [cursorVersion, setCursorVersion] = useState("");
  const [schemeName, setSchemeName] = useState("");
  const [role, setRole] = useState("Arrow");
  const imageInput = useRef<HTMLInputElement>(null);
  const cursorInput = useRef<HTMLInputElement>(null);
  const folderInput = useRef<HTMLInputElement>(null);
  const chooseScheme = (value: CursorScheme) => { setScheme(value.id); setRoles(value.roles); setSize(value.size); };
  const refresh = async (resetCursors = false) => {
    const next = await client.call<DesktopState>("state");
    setState(next);
    if (resetCursors && next.cursors.schemes[0]) { chooseScheme(next.cursors.schemes[0]); setCursorVersion(next.cursors.version); }
    setSelected((ids) => ids.filter((id) => next.shortcuts.some((item) => item.id === id)));
  };
  const run = async (action: () => Promise<void>, section: "icons" | "cursors" = "icons") => {
    if (running.current) return;
    running.current = true; setBusy(true); setMessage(null); setMessageFor(section);
    try { await action(); }
    catch (error) {
      const key = error instanceof Error ? error.message : String(error);
      setMessage({ text: ["desktop_unavailable", "desktop_reconnect", "file_too_large", "read_failed"].includes(key) ? tt(key) : key, error: true });
    } finally { running.current = false; setBusy(false); }
  };
  useEffect(() => { void run(() => refresh(true)); }, [client]);
  const reportChanges = (result: ChangeResult, restored = false) => {
    const success = result.entries.filter((e) => e.status === (restored ? "restored" : "applied")).length;
    const failures = result.entries.filter((e) => e.status !== (restored ? "restored" : "applied"));
    setMessage({ text: tt(restored ? "icons_restored" : "icons_applied", { count: success }) +
      (failures.length ? "\n" + failures.map((e) => `${e.name}：${e.error || e.status}`).join("\n") : ""), error: !!failures.length });
  };
  const importImage = (file?: File) => {
    if (!file) return;
    void run(async () => {
      const item = await client.call<Artwork>("icons.import", await uploadFile(file));
      setArtwork(item);
      setState((old) => old ? { ...old, icons: [...old.icons.filter((i) => i.id !== item.id), item] } : old);
      setMessage({ text: tt("image_ready"), error: false });
    });
  };
  const importCursors = (files: FileList | null, forRole?: string) => {
    if (!files?.length) return;
    const chosen = Array.from(files).filter((file) => /\.(cur|ani)$/i.test(file.name));
    void run(async () => {
      if (!chosen.length) throw new Error(tt("choose_cursor_files"));
      if (chosen.reduce((sum, f) => sum + f.size, 0) > 32 * 1024 * 1024) throw new Error("file_too_large");
      const result = await client.call<CursorImport>("cursors.import", { files: await Promise.all(chosen.map(uploadFile)), role: forRole });
      setRoles((old) => ({ ...old, ...result.roles })); setScheme("");
      setState((old) => old ? { ...old, cursors: { ...old.cursors, resources: { ...old.cursors.resources, ...result.resources } } } : old);
      setMessage({ text: tt("cursor_imported", { count: result.matched, total: result.total }), error: !result.matched });
    }, "cursors");
  };
  const visible = state?.shortcuts.filter((item) => item.name.toLocaleLowerCase().includes(search.toLocaleLowerCase())) || [];
  const cursorResource = state?.cursors.resources[roles[role] || ""];
  const schemeLabel = (item: CursorScheme) => item.kind === "current" ? tt("current_cursors") : item.kind === "default" ? tt("default_cursors") : item.name;

  return <>
    <section id="workbench-desktop" className={`${groupStyles.group} ${cs.section}`}>
      <div className={cs.heading}><div><h2>{tt("icons_title")}</h2><p>{tt("icons_description")}</p></div><span className={cs.live}>{tt("windows_live")}</span></div>
      {message && messageFor === "icons" && <div role={message.error ? "alert" : "status"} className={`${cs.message} ${message.error ? cs.error : ""}`}>{message.text}</div>}
      {!state && <p>{busy ? tt("loading") : tt("desktop_unavailable")}</p>}
      <fieldset disabled={busy} className={cs.fieldset}>
        <div className={cs.toolbar}>
          <input type="search" placeholder={tt("search_icons")} aria-label={tt("search_icons")} value={search} onInput={(e) => setSearch(e.currentTarget.value)} />
          <button onClick={() => void run(() => refresh(!state))}>{tt("refresh_icons")}</button>
          <button disabled={!visible.length} onClick={() => setSelected(Array.from(new Set([...selected, ...visible.map((s) => s.id)])))}>{tt("select_visible")}</button>
          <button disabled={!selected.length} onClick={() => setSelected([])}>{tt("clear_selection")}</button>
        </div>
        <div className={cs.iconLayout}>
          <div className={cs.shortcuts} aria-label={tt("desktop_shortcuts")}>
            {visible.map((item) => <label key={item.id} className={selected.includes(item.id) ? cs.selected : ""}>
              <input type="checkbox" aria-label={tt("select_shortcut", { name: item.name })} checked={selected.includes(item.id)} onChange={(e) => setSelected(e.currentTarget.checked ? [...selected, item.id] : selected.filter((id) => id !== item.id))} />
              <img src={item.preview} alt="" width="36" height="36" />
              <span><strong>{item.name}</strong><small>{item.origin} · {item.kind}</small></span>
            </label>)}
            {state && !visible.length && <p>{tt("no_shortcuts")}</p>}
          </div>
          <div className={cs.artwork}>
            <div className={cs.artworkPreview}>{artwork ? <img src={artwork.preview} alt={artwork.name} /> : <span>✦</span>}</div>
            <strong>{artwork?.name || tt("choose_artwork")}</strong>
            <p>{tt("image_formats")}</p>
            <button disabled={!state} onClick={() => imageInput.current?.click()}>{tt("choose_image")}</button>
            <input ref={imageInput} hidden type="file" accept=".png,.jpg,.jpeg,.webp,.bmp,.gif,.tif,.tiff,.ico" onChange={(e) => { importImage(e.currentTarget.files?.[0]); e.currentTarget.value = ""; }} />
            <button className={cs.primary} disabled={!selected.length || !artwork} onClick={() => void run(async () => {
              const result = await client.call<ChangeResult>("icons.apply", { icon: artwork!.id, items: state!.shortcuts.filter((s) => selected.includes(s.id)).map(({ id, sha256 }) => ({ id, sha256 })) });
              await refresh(); setSelected([]); reportChanges(result);
            })}>{tt("replace_icons", { count: selected.length })}</button>
            <small>{tt("icon_backup_notice")}</small>
          </div>
        </div>
        {!!state?.icons.length && <details><summary>{tt("saved_images", { count: state.icons.length })}</summary><div className={cs.library}>{state.icons.map((item) => <button key={item.id} aria-label={tt("use_image", { name: item.name })} className={artwork?.id === item.id ? cs.selected : ""} onClick={() => setArtwork(item)}><img src={item.preview} alt="" /><span>{item.name}</span></button>)}</div></details>}
        {!!state?.history.length && <details><summary>{tt("icon_history")}</summary><div className={cs.history}>{state.history.map((item) => <div key={item.id}><span>{item.created} · {tt("item_count", { count: item.count })}</span><button onClick={() => void run(async () => {
          const result = await client.call<ChangeResult>("icons.restore", { id: item.id }); await refresh(); reportChanges(result, true);
        })}>{tt("restore_batch")}</button></div>)}</div></details>}
      </fieldset>
      {!!state?.errors.length && <details className={cs.issues}><summary>{tt("read_issues", { count: state.errors.length })}</summary>{state.errors.map((error, i) => <p key={i}>{error}</p>)}</details>}
    </section>
    <section id="workbench-cursors" className={`${groupStyles.group} ${cs.section}`}>
      <div className={cs.heading}><div><h2>{tt("cursors_title")}</h2><p>{tt("cursors_description")}</p></div><span className={cs.live}>{tt("windows_live")}</span></div>
      {message && messageFor === "cursors" && <div role={message.error ? "alert" : "status"} className={`${cs.message} ${message.error ? cs.error : ""}`}>{message.text}</div>}
      <fieldset disabled={busy || !state} className={cs.fieldset}>
        <div className={cs.toolbar}>
          <label>{tt("scheme")}<select aria-label={tt("scheme")} value={scheme} onChange={(e) => { const next = state?.cursors.schemes.find((s) => s.id === e.currentTarget.value); if (next) chooseScheme(next); }}>
            <option value="" disabled>{tt("custom_scheme")}</option>{state?.cursors.schemes.map((s) => <option key={s.id} value={s.id}>{schemeLabel(s)}</option>)}
          </select></label>
          <label>{tt("cursor_size")}<select aria-label={tt("cursor_size")} value={size} onChange={(e) => setSize(Number(e.currentTarget.value))}>{Array.from({ length: 15 }, (_, i) => 32 + i * 16).map((v) => <option value={v} key={v}>{v} px</option>)}</select></label>
          <button onClick={() => void run(async () => { await refresh(true); setMessage({ text: tt("cursors_loaded"), error: false }); }, "cursors")}>{tt("read_current")}</button>
          <button onClick={() => folderInput.current?.click()}>{tt("import_cursor_folder")}</button>
          <input ref={(node) => { folderInput.current = node; node?.setAttribute("webkitdirectory", ""); }} hidden type="file" multiple accept=".cur,.ani" onChange={(e) => { importCursors(e.currentTarget.files); e.currentTarget.value = ""; }} />
        </div>
        <div className={cs.cursorLayout}>
          <div className={cs.roleGrid}>{state?.cursors.roles.map((key) => <button key={key} className={role === key ? cs.selected : ""} onClick={() => setRole(key)} aria-pressed={role === key}>
            {state.cursors.resources[roles[key] || ""] ? <img src={state.cursors.resources[roles[key]!]!.preview} alt="" /> : <span className={cs.defaultIcon}>↖</span>}
            <span>{tt(`roles.${key}`)}</span>
          </button>)}</div>
          <div className={cs.cursorDetail}>
            <strong>{tt(`roles.${role}`)}</strong>
            {cursorResource && <img src={cursorResource.preview} alt={tt(`roles.${role}`)} width="64" height="64" />}
            <p>{cursorResource?.name || tt("system_default")}</p>
            <button onClick={() => cursorInput.current?.click()}>{tt("replace_cursor")}</button>
            <button onClick={() => { const defaults = state!.cursors.schemes.find((s) => s.kind === "default"); setRoles({ ...roles, [role]: defaults?.roles[role] || "" }); setScheme(""); }}>{tt("reset_role")}</button>
            <input ref={cursorInput} hidden type="file" accept=".cur,.ani" onChange={(e) => { importCursors(e.currentTarget.files, role); e.currentTarget.value = ""; }} />
          </div>
        </div>
        <div className={cs.toolbar}>
          <input aria-label={tt("scheme_name")} placeholder={tt("scheme_name")} value={schemeName} maxLength={120} onInput={(e) => setSchemeName(e.currentTarget.value)} />
          <button disabled={!schemeName.trim()} onClick={() => void run(async () => {
            const item = await client.call<CursorScheme>("cursors.save", { roles, size, name: schemeName }); await refresh(); chooseScheme(item); setMessage({ text: tt("scheme_saved"), error: false });
          }, "cursors")}>{tt("save_scheme")}</button>
          <button className={cs.primary} onClick={() => void run(async () => { await client.call("cursors.apply", { roles, size, version: cursorVersion }); await refresh(true); setMessage({ text: tt("cursors_applied"), error: false }); }, "cursors")}>{tt("apply_cursors")}</button>
          <button disabled={!state?.cursors.canRestore} onClick={() => void run(async () => { await client.call("cursors.restore"); await refresh(true); setMessage({ text: tt("cursors_restored"), error: false }); }, "cursors")}>{tt("restore_cursors")}</button>
        </div>
        <p className={cs.note}>{tt("cursor_notice")}</p>
      </fieldset>
    </section>
  </>;
}
