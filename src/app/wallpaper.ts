// SPDX-License-Identifier: AGPL-3.0-or-later
// Desktop playback uses Seelen's actual image/video components and the existing
// Windhawk motion port, exactly as the settings preview does.
import { mount } from "svelte";
import MediaSurface from "../../vendor/Seelen-UI/libs/ui/svelte/components/Wallpaper/ParallaxPreview.svelte";
import { DEFAULT_PARALLAX, parseParallax, type ParallaxSettings, type Rect } from "../../vendor/Seelen-UI/libs/ui/shared/wallpaper-parallax/motion.ts";

interface Surface {
  setMedia(kind: "image" | "video", source: string): Promise<void>;
  setOptions(settings: ParallaxSettings): void;
  setPaused(paused: boolean): Promise<void>;
  setPointer(x: number, y: number, bounds: Rect): void;
}
interface WallpaperCommand {
  operation: "apply" | "pointer";
  requestId?: string;
  media?: { id: string; name: string; kind: "image" | "video"; animated?: boolean; url: string };
  settings?: ParallaxSettings;
  paused?: boolean;
  x?: number;
  y?: number;
  bounds?: Rect;
}
const native = (window as unknown as { chrome: { webview: {
  postMessage(value: unknown): void;
  addEventListener(type: "message", callback: (event: MessageEvent<WallpaperCommand>) => void): void;
} } }).chrome.webview;
const surface = mount(MediaSurface, { target: document.getElementById("root")!, props: { initialSettings: DEFAULT_PARALLAX, desktop: true } }) as unknown as Surface;
let revision = 0;
let currentMedia = "";
const waitForMedia = async (kind: "image" | "video") => {
  const element = document.querySelector(kind === "video" ? "video" : "img") as HTMLVideoElement | HTMLImageElement | null;
  if (!element) throw new Error("wallpaper_media_missing");
  const loaded = () => element instanceof HTMLVideoElement ? element.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA : element.complete && element.naturalWidth > 0;
  if (loaded()) return;
  await new Promise<void>((resolve, reject) => {
    const finish = (error?: Error) => { clearTimeout(timeout); element.removeEventListener("load", onLoad); element.removeEventListener("loadeddata", onLoad); element.removeEventListener("error", onError); error ? reject(error) : resolve(); };
    const onLoad = () => finish();
    const onError = () => finish(new Error("wallpaper_decode_failed"));
    const timeout = setTimeout(() => finish(new Error("wallpaper_load_timeout")), 20000);
    element.addEventListener("load", onLoad, { once: true });
    element.addEventListener("loadeddata", onLoad, { once: true });
    element.addEventListener("error", onError, { once: true });
    if (loaded()) finish();
  });
};
native.addEventListener("message", async ({ data }) => {
  if (data.operation === "pointer") {
    if (data.bounds && typeof data.x === "number" && typeof data.y === "number") surface.setPointer(data.x, data.y, data.bounds);
    return;
  }
  const ownRevision = ++revision;
  try {
    if (!data.media || !data.requestId) throw new Error("wallpaper_request_invalid");
    const source = new URL(data.media.url);
    if (source.protocol !== "https:" || source.hostname !== "media.theme-studio.invalid") throw new Error("wallpaper_source_invalid");
    if (currentMedia !== data.media.id) {
      await surface.setMedia(data.media.kind, data.media.url);
      await waitForMedia(data.media.kind);
      currentMedia = data.media.id;
    }
    if (ownRevision !== revision) return;
    surface.setOptions(parseParallax(data.settings));
    await surface.setPaused(!!data.paused);
    const video = document.querySelector("video");
    if (video && !data.paused) await video.play();
    native.postMessage({ operation: "wallpaper.applied", requestId: data.requestId, mediaId: currentMedia, kind: data.media.kind, playing: video ? !video.paused : !!data.media.animated && !data.paused });
  } catch (error) {
    if (ownRevision === revision) native.postMessage({ operation: "wallpaper.error", requestId: data.requestId, error: error instanceof Error ? error.message : String(error) });
  }
});
native.postMessage({ operation: "wallpaper.ready" });
