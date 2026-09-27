import { useEffect, useRef, useState } from "preact/hooks";
import { useTranslation } from "react-i18next";
import { mount, unmount } from "svelte";
import MediaSurface from "../../../../../../../libs/ui/svelte/components/Wallpaper/ParallaxPreview.svelte";
import { PRESETS } from "../../../../../../../libs/ui/shared/wallpaper-parallax/motion.ts";
import type { ParallaxSettings } from "../../../../../../../libs/ui/shared/wallpaper-parallax/motion.ts";
import styles from "./parallax.module.css";

interface SurfaceApi {
  setOptions(settings: ParallaxSettings): void;
  setMedia(kind: "image" | "video", source: string): Promise<void>;
  setPaused(paused: boolean): void;
}
export function ParallaxPanel({ settings, onChange }: { settings: ParallaxSettings; onChange: (s: ParallaxSettings) => void }) {
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

  useEffect(() => {
    alive.current = true;
    const instance = mount(MediaSurface, { target: host.current!, props: { initialSettings: settings, onMediaError: () => { if (alive.current) setError(p("load_failed")); } } });
    surface.current = instance as unknown as SurfaceApi;
    return () => {
      alive.current = false; selection.current++; surface.current = null;
      const owned = objectUrl.current; objectUrl.current = null;
      void unmount(instance).finally(() => { if (owned) URL.revokeObjectURL(owned); });
    };
  }, []);
  useEffect(() => surface.current?.setOptions(settings), [settings]);

  const changeMedia = async (type: "image" | "video", source: string, name: string | null, owned = false) => {
    const revision = ++selection.current;
    const previous = objectUrl.current;
    objectUrl.current = owned ? source : null;
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
  const update = (patch: Partial<ParallaxSettings>) => onChange({ ...settings, ...patch });

  return <section id="workbench-parallax" className={styles.panel}>
    <div className={styles.heading}><div><h2>{p("title")}</h2><p>{p("description")}</p></div>
      <label className={styles.enable}><input type="checkbox" checked={settings.enabled} onChange={(e) => update({ enabled: e.currentTarget.checked })} />{p("enabled")}</label>
    </div>
    <div className={styles.body}>
      <div>
        <div ref={host} className={styles.surface} aria-label={p("surface")} />
        <p className={styles.caption}>{p(settings.enabled ? "move_pointer" : "effect_off")}</p>
        <div className={styles.mediaButtons}>
          <button type="button" onClick={() => void changeMedia("image", "./fixtures/parallax-landscape.svg", null)}>{p("example_image")}</button>
          <button type="button" onClick={() => void changeMedia("video", "./fixtures/parallax-motion.mp4", null)}>{p("example_video")}</button>
          <button type="button" onClick={() => fileInput.current?.click()}>{p("choose_file")}</button>
          <button type="button" disabled={kind !== "video"} onClick={() => { surface.current?.setPaused(!paused); setPaused(!paused); }}>{p(paused ? "resume" : "pause")}</button>
          <input type="file" accept="image/*,video/*" ref={fileInput} hidden onChange={(e) => selectFile(e.currentTarget.files?.[0])} />
        </div>
        <p className={styles.caption}>{filename || p(kind === "video" ? "sample_video" : "sample_image")}</p>
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
