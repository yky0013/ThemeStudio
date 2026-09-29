<script lang="ts">
  import { convertFileSrc } from "@tauri-apps/api/core";
  import type { DefinedWallProps } from "../types";
  import { getWallpaperStyles } from "../appearance.ts";

  let { definition, config, onLoad, onError, sourceOverride, paused = false }: DefinedWallProps = $props();
  let element = $state<HTMLImageElement>();
  let still = $state<HTMLCanvasElement>();
  let frozen = $state(false);

  const imageSrc = $derived(sourceOverride ?? convertFileSrc(definition.metadata.path + "\\" + definition.filename!));

  function freezeFrame() {
    if (!paused || !element?.complete || !element.naturalWidth || !still) { frozen = false; return; }
    still.width = element.naturalWidth; still.height = element.naturalHeight;
    const context = still.getContext('2d');
    if (context) { context.drawImage(element, 0, 0); frozen = true; }
  }
  $effect(() => { imageSrc; paused; freezeFrame(); });
  function loaded() { freezeFrame(); onLoad?.(); }

  function handleError(e: Event) {
    onError?.();
    const target = e.target as HTMLImageElement;
    console.error("Image failed to load:", {
      src: imageSrc,
      naturalWidth: target.naturalWidth,
      naturalHeight: target.naturalHeight,
    });
  }
</script>

<div class="image-surface"><img
  bind:this={element}
  id={definition.id}
  class="wallpaper"
  style={getWallpaperStyles(config)}
  style:visibility={frozen ? 'hidden' : 'visible'}
  src={imageSrc}
  crossOrigin="anonymous"
  onload={loaded}
  onerror={handleError}
  decoding="async"
  loading="eager"
  alt=""
/><canvas bind:this={still} class="wallpaper frozen" style={getWallpaperStyles(config)} hidden={!frozen}></canvas></div>

<style>
  .wallpaper {
    position: relative;
    width: 100%;
    height: 100%;
  }
  .image-surface { width: 100%; height: 100%; position: relative; }
  .frozen { position: absolute; inset: 0; }
</style>
