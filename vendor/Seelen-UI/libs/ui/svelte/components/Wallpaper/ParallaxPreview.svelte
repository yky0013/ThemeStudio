<script lang="ts">
  import { tick, untrack } from "svelte";
  import type { Wallpaper, WallpaperInstanceSettings } from "@seelen-ui/lib/types";
  import type { ParallaxSettings, Rect } from "../../../shared/wallpaper-parallax/motion.ts";
  import ParallaxLayer from "./ParallaxLayer.svelte";
  import ImageWallpaper from "./components/ImageWallpaper.svelte";
  import VideoWallpaper from "./components/VideoWallpaper.svelte";

  let { initialSettings, onMediaError, onMediaLoad, desktop = false }:
    { initialSettings: ParallaxSettings; onMediaError?: () => void; onMediaLoad?: () => void; desktop?: boolean } = $props();
  let settings = $state(untrack(() => initialSettings));
  let source = $state("./fixtures/parallax-landscape.svg");
  let kind = $state<"image" | "video">("image");
  let paused = $state(false);
  let pointer = $state<[number, number] | null>(null);
  let sourceBounds = $state<Rect | undefined>(undefined);
  // A preview resource only supplies an element id. sourceOverride keeps the
  // original media components away from Tauri file conversion in the browser.
  const definition = { id: "@workbench/preview", metadata: { path: "" }, filename: "preview" } as Wallpaper;
  const config = {
    playbackSpeed: "x1", flipHorizontal: false, flipVertical: false, blur: 0,
    objectFit: "cover", objectPosition: "center", saturation: 1, contrast: 1,
    withOverlay: false, overlayMixBlendMode: "multiply", overlayColor: "#ff0000", muted: true,
  } as WallpaperInstanceSettings;

  export function setOptions(next: ParallaxSettings) { settings = next; }
  export async function setPaused(next: boolean) { paused = next; await tick(); }
  export function setPointer(x: number, y: number, bounds: Rect) { pointer = [x, y]; sourceBounds = bounds; }
  export async function setMedia(nextKind: "image" | "video", nextSource: string) {
    kind = nextKind; source = nextSource; paused = false;
    await tick();
  }
</script>

<ParallaxLayer options={settings} {paused} {pointer} {sourceBounds} localPointer={!desktop}>
  {#if kind === "video"}
    <VideoWallpaper {definition} {config} {paused} muted sourceOverride={source} onLoad={onMediaLoad} onError={onMediaError} />
  {:else}
    <ImageWallpaper {definition} {config} {paused} sourceOverride={source} onLoad={onMediaLoad} onError={onMediaError} />
  {/if}
</ParallaxLayer>
