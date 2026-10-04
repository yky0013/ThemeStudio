import { useEffect, useRef, useState } from "preact/hooks";
import { useTranslation } from "react-i18next";
import { mount, unmount } from "svelte";
import MediaSurface from "../../../../../../../libs/ui/svelte/components/Wallpaper/ParallaxPreview.svelte";
import { PRESETS } from "../../../../../../../libs/ui/shared/wallpaper-parallax/motion.ts";
import type { ParallaxSettings } from "../../../../../../../libs/ui/shared/wallpaper-parallax/motion.ts";
import styles from "./parallax.module.css";
import type { DesktopClient } from "../domain/desktop.ts";
import { appearanceDraft } from '../domain/appearance.ts';

interface SurfaceApi {
  setOptions(settings: ParallaxSettings): void;
  setMedia(kind: "image" | "video", source: string): Promise<void>;
  setPaused(paused: boolean): void;
}
interface WallpaperMedia { id: string; name: string; kind: "image" | "video"; url: string }
interface WallpaperState { active: boolean; paused?: boolean; mode?: string; media?: WallpaperMedia; settings?: ParallaxSettings }
export function ParallaxPanel({ settings, onChange, desktopClient, desktopNative = false, unified=false }:
  { settings: ParallaxSettings; onChange: (s: ParallaxSettings) => void; desktopClient?: DesktopClient; desktopNative?: boolean; unified?:boolean }) {
  const { t } = useTranslation();
  const p = (key: string) => t(`theme_workbench.parallax.${key}`);
  const host = useRef<HTMLDivElement>(null);
  const surface = useRef<SurfaceApi | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const objectUrl = useRef<string | null>(null);
  const alive = useRef(true);
  const selection = useRef(0);
  const [kind, setKind] = useState<"image" | "video">("image");
  const [filename, setFilename] = useState<string | null>(null);
  const [paused, setPaused] = useState(false);
  const [error, setError] = useState("");
  const [media, setMedia] = useState<WallpaperMedia | null>(null);
  const [desktop, setDesktop] = useState<WallpaperState>({ active: false });
  const [desktopBusy, setDesktopBusy] = useState(false);
  const [dirty,setDirty]=useState(false);
  const [useWallpaper,setUseWallpaper]=useState(false);
  const desktopRunning = useRef(false);
  const selectedSource = useRef({kind: "image" as "image" | "video", url: "./fixtures/parallax-landscape.svg"});
  const pausedRef = useRef(false);
  const settingsRef = useRef(settings);
  settingsRef.current = settings; pausedRef.current = paused;

  useEffect(() => {
    alive.current = true;
    let instance: ReturnType<typeof mount> | null = null;
    let visible = false;
    const visibility = () => surface.current?.setPaused(pausedRef.current || !visible || document.hidden);
    const observer = new IntersectionObserver(entries => {
      visible = entries.some(entry => entry.isIntersecting);
      if (visible && !instance) {
        instance = mount(MediaSurface, { target: host.current!, props: { initialSettings: settingsRef.current,
          onMediaError: () => { if (alive.current) setError(p("load_failed")); },
          onMediaLoad: () => { if (alive.current) setError(""); } } });
        surface.current = instance as unknown as SurfaceApi;
        void surface.current.setMedia(selectedSource.current.kind, selectedSource.current.url).then(visibility);
      }
      visibility();
    }, {rootMargin:"180px"});
    observer.observe(host.current!);
    document.addEventListener("visibilitychange", visibility);
    return () => {
      alive.current = false; selection.current++; surface.current = null;
      const owned = objectUrl.current; objectUrl.current = null;
      observer.disconnect(); document.removeEventListener("visibilitychange", visibility);
      if (instance) void unmount(instance).finally(() => { if (owned) URL.revokeObjectURL(owned); });
      else if (owned) URL.revokeObjectURL(owned);
    };
  }, []);
  useEffect(() => surface.current?.setOptions(settings), [settings]);
  useEffect(() => {
    if (!desktopNative || !desktopClient) return;
    const refresh = () => { void desktopClient.call<WallpaperState>("wallpaper.status").then(async (state) => {
      if (!alive.current) return;
      setDesktop(state);setDirty(false);setUseWallpaper(state.active);
      if (state.media) { setMedia(state.media); await changeMedia(state.media.kind, state.media.url, state.media.name); }
      if (state.active && state.settings) onChange(state.settings);
    }).catch((failure) => { if (alive.current) setError(String(failure)); }); };
    refresh();
    document.addEventListener("theme-studio-template-applied", refresh);
    document.addEventListener('theme-studio-draft-discarded',refresh);
    return () => {document.removeEventListener("theme-studio-template-applied", refresh);document.removeEventListener('theme-studio-draft-discarded',refresh);};
  }, [desktopClient, desktopNative]);

  const changeMedia = async (type: "image" | "video", source: string, name: string | null, owned = false) => {
    const revision = ++selection.current;
    const previous = objectUrl.current;
    objectUrl.current = owned ? source : null;
    selectedSource.current = {kind:type,url:source};
    try {
      await surface.current?.setMedia(type, source);
      if (alive.current && selection.current === revision) { setKind(type); setFilename(name); setPaused(false); setError(""); }
    } catch (failure) { if (alive.current) setError(String(failure)); }
    finally { if (previous && previous !== source) URL.revokeObjectURL(previous); }
  };
  const selectFile = (file?: File) => {
    if (!file) return;
    const type = file.type.startsWith("video/") ? "video" : file.type.startsWith("image/") ? "image" : null;
    if (!type) { setError(p("unsupported")); return; }
    void changeMedia(type, URL.createObjectURL(file), file.name, true);
    if (fileInput.current) fileInput.current.value = "";
  };
  const update = (patch: Partial<ParallaxSettings>) => {setDirty(true);setUseWallpaper(true);onChange({ ...settings, ...patch });};
  const runDesktop = async (action: () => Promise<void>) => {
    if (desktopRunning.current) return;
    desktopRunning.current = true; setDesktopBusy(true); setError("");
    try { await action(); } catch (failure) { if (alive.current) setError(failure instanceof Error ? failure.message : String(failure)); }
    finally { desktopRunning.current = false; if (alive.current) setDesktopBusy(false); }
  };
  const chooseExample = (type: "image" | "video") => {
    if (!desktopNative || !desktopClient) { void changeMedia(type, type === "video" ? "./fixtures/parallax-motion.mp4" : "./fixtures/parallax-landscape.svg", null); return; }
    void runDesktop(async () => { const resource = await desktopClient.call<WallpaperMedia>("wallpaper.example", { kind: type }); setMedia(resource);setDirty(true);setUseWallpaper(true); await changeMedia(type, resource.url, resource.name); });
  };
  const chooseLocal = () => {
    if (!desktopNative || !desktopClient) { fileInput.current?.click(); return; }
    void runDesktop(async () => { const resource = await desktopClient.call<WallpaperMedia | null>("wallpaper.pick"); if (!resource) return; setMedia(resource);setDirty(true);setUseWallpaper(true); await changeMedia(resource.kind, resource.url, resource.name); });
  };
  useEffect(() => {
    const importRequested = () => chooseLocal();
    document.addEventListener('theme-studio-import-wallpaper', importRequested);
    return () => document.removeEventListener('theme-studio-import-wallpaper', importRequested);
  }, [desktopClient, desktopNative]);
  useEffect(()=>{
    if(unified&&dirty)appearanceDraft.set('wallpaper',{label:p('title'),operation:useWallpaper?'wallpaper.apply':'wallpaper.stop',
      payload:useWallpaper?{mediaId:media?.id,useExample:!media,kind,settings,paused:false}:{},error:desktopBusy?p('applying'):undefined});
  },[unified,dirty,useWallpaper,media,kind,settings,desktopBusy]);

  return <section id="workbench-parallax" className={styles.panel}>
    <div className={styles.heading}><div><h2>{p("title")}</h2><p>{p("description")}</p></div>
      <label className={styles.enable}><input type="checkbox" checked={settings.enabled} onChange={(e) => update({ enabled: e.currentTarget.checked })} />{p("enabled")}</label>
    </div>
    <div className={styles.body}>
      <div>
        <div ref={host} className={styles.surface} aria-label={p("surface")} />
        <p className={styles.caption}>{p(settings.enabled ? "move_pointer" : "effect_off")}</p>
        <div className={styles.mediaButtons}>
          <button type="button" disabled={desktopBusy} onClick={() => chooseExample("image")}>{p("example_image")}</button>
          <button type="button" disabled={desktopBusy} onClick={() => chooseExample("video")}>{p("example_video")}</button>
          <button type="button" disabled={desktopBusy} onClick={chooseLocal}>{p("choose_file")}</button>
          <button type="button" onClick={() => { surface.current?.setPaused(!paused); setPaused(!paused); }}>{p(paused ? "resume" : "pause")}</button>
          <input type="file" accept="image/*,video/*" ref={fileInput} hidden onChange={(e) => selectFile(e.currentTarget.files?.[0])} />
        </div>
        <p className={styles.caption}>{filename || p(kind === "video" ? "sample_video" : "sample_image")}</p>
        {!unified&&<div className={styles.mediaButtons}>
          <button type="button" disabled={!desktopNative || desktopBusy} onClick={() => void runDesktop(async () => {
            const resource = media || await desktopClient!.call<WallpaperMedia>("wallpaper.example", { kind });
            setMedia(resource);
            const result = await desktopClient!.call<WallpaperState>("wallpaper.apply", { mediaId: resource.id, settings, paused: false });
            setDesktop(result);
          })}>{p(desktopBusy ? "applying" : "apply_desktop")}</button>
          <button type="button" disabled={!desktop.active || desktopBusy || desktop.mode === "static"} onClick={() => void runDesktop(async () => { setDesktop(await desktopClient!.call<WallpaperState>("wallpaper.pause", { paused: !desktop.paused })); })}>{p(desktop.paused ? "resume_desktop" : "pause_desktop")}</button>
          <button type="button" disabled={!desktop.active || desktopBusy} onClick={() => void runDesktop(async () => { setDesktop(await desktopClient!.call<WallpaperState>("wallpaper.stop")); })}>{p("restore_desktop")}</button>
        </div>}
        {unified&&<label><input type="checkbox" checked={useWallpaper} onChange={e=>{setDirty(true);setUseWallpaper(e.currentTarget.checked);}}/> {p('use_desktop_draft')}</label>}
        <p role="status" className={styles.caption}>{desktop.active && desktop.mode === "static" ? "静态省内存模式：由 Windows 显示壁纸，无需后台播放进程。" : p(!desktopNative ? "native_required" : desktop.active ? desktop.paused ? "desktop_paused" : "desktop_active" : "desktop_inactive")}</p>
        {error && <p role="alert">{error}</p>}
      </div>
      <div className={styles.controls}>
        <label>{p("preset")}<select aria-label={p("preset")} value={settings.preset} onChange={(e) => update({ preset: e.currentTarget.value as ParallaxSettings["preset"] })}>
          {Object.keys(PRESETS).map((preset) => <option value={preset} key={preset}>{p(preset)}</option>)}
        </select></label>
        <label>{p("strength")} <output>{settings.strength.toFixed(1)}×</output>
          <input type="range" aria-label={p("strength")} min="0" max="2" step="0.1" value={settings.strength} onInput={(e) => update({ strength: Number(e.currentTarget.value) })} />
        </label>
        <label className={styles.check}><input type="checkbox" checked={settings.perspective} onChange={(e) => update({ perspective: e.currentTarget.checked })} />{p("perspective")}</label>
        <label>{p("tilt")} <output>{settings.tilt}°</output>
          <input type="range" aria-label={p("tilt")} min="0" max="8" step="0.5" disabled={!settings.perspective} value={settings.tilt} onInput={(e) => update({ tilt: Number(e.currentTarget.value) })} />
        </label>
        <label className={styles.check}><input type="checkbox" checked={settings.opposite} onChange={(e) => update({ opposite: e.currentTarget.checked })} />{p("opposite")}</label>
        <p className={styles.caption}>{p("media_notice")}</p>
      </div>
    </div>
  </section>;
}
