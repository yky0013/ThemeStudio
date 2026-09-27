// SPDX-License-Identifier: AGPL-3.0-or-later
import { useEffect, useRef, useState } from "preact/hooks";
import { useTranslation } from "react-i18next";
import type { DesktopClient } from "../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts";
import type { ThemeRecipe } from "../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/model.ts";
import cs from "./studio.module.css";

export interface RuntimeState {
  seelen: { available: boolean; running: boolean; dock: boolean; toolbar: boolean; version: string };
  windhawk: { available: boolean; running: boolean; compiler: boolean; version: string; error?: string;
    mods: { id: string; name: string; enabled: boolean; loaded: boolean }[] };
}
export function RuntimePanel({ client, recipe, native, onState }:
  { client: DesktopClient; recipe: ThemeRecipe; native: boolean; onState: (state: RuntimeState) => void }) {
  const { t } = useTranslation();
  const rt = (key: string, values?: Record<string, unknown>) => t(`theme_workbench.runtime.${key}`, values);
  const [state, setState] = useState<RuntimeState | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState("");
  const running = useRef(false);
  const alive = useRef(true);
  const refresh = async () => {
    const next = await client.call<RuntimeState>("runtime.state");
    if (alive.current) { setState(next); onState(next); }
  };
  useEffect(() => {
    alive.current = true;
    if (!native) return;
    void refresh().catch((failure) => setError(String(failure)));
    const timer = setInterval(() => { if (!running.current) void refresh().catch(() => {}); }, 5000);
    const report = (event: Event) => {
      const detail = (event as CustomEvent<{ stage: string; name: string }>).detail;
      setProgress(rt(`progress.${detail.stage}`, { name: detail.name }));
    };
    document.addEventListener("theme-studio-runtime-progress", report);
    return () => { alive.current = false; clearInterval(timer); document.removeEventListener("theme-studio-runtime-progress", report); };
  }, [client, native]);
  const run = async (operation: string, payload?: unknown) => {
    if (running.current) return;
    running.current = true; setBusy(true); setError(""); setProgress(rt("working"));
    try { await client.call(operation, payload); await refresh(); }
    catch (failure) { if (alive.current) setError(failure instanceof Error ? failure.message : String(failure)); }
    finally { running.current = false; if (alive.current) { setBusy(false); setProgress(""); } }
  };
  return <div className={cs.enginePanel}>
    <div className={cs.engineHeading}><h3>{rt("title")}</h3><button disabled={!native || busy} onClick={() => void refresh().catch((failure) => setError(String(failure)))}>{rt("refresh")}</button></div>
    {!native && <p>{rt("native_required")}</p>}
    {error && <p role="alert" className={cs.engineError}>{error}</p>}
    {busy && <p role="status">{progress}</p>}
    <div className={cs.engineCards}>
      <div><h4>Seelen Dock / Toolbar</h4><p>{rt("seelen_chosen")}</p>
        <p role="status">{rt(state?.seelen.dock && state?.seelen.toolbar ? "seelen_active" : state?.seelen.available ? "seelen_off" : "unavailable")}</p>
        <div className={cs.engineActions}><button disabled={!native || busy || !state?.seelen.available} onClick={() => void run("runtime.seelen.apply", { seelen: recipe.seelen })}>{rt("seelen_enable")}</button>
          <button disabled={!native || busy || (!state?.seelen.dock && !state?.seelen.toolbar)} onClick={() => void run("runtime.seelen.stop")}>{rt("seelen_disable")}</button></div>
      </div>
      <div><h4>Windhawk</h4><p>{rt("mod_selection", { count: recipe.windhawk.length })}</p>
        <p role="status">{rt(state?.windhawk.running ? "windhawk_active" : state?.windhawk.available ? "windhawk_off" : "unavailable")}</p>
        <div className={cs.engineActions}><button disabled={!native || busy || !recipe.windhawk.length || !state?.windhawk.compiler} onClick={() => void run("runtime.windhawk.apply", { mods: recipe.windhawk })}>{rt("mods_enable")}</button>
          <button disabled={!native || busy || !state?.windhawk.mods.some((item) => item.enabled)} onClick={() => void run("runtime.windhawk.stop")}>{rt("mods_disable")}</button></div>
      </div>
    </div>
    {!!state?.windhawk.mods.length && <div className={cs.modStatus}>{state.windhawk.mods.map((mod) => <div key={mod.id}><span>{mod.name || mod.id.replace(/^local@/, "")}</span><strong>{rt(!mod.enabled ? "mod_disabled" : mod.loaded ? "mod_loaded" : "mod_waiting")}</strong></div>)}</div>}
    <p className={cs.engineNote}>{rt("notice")}</p>
  </div>;
}
