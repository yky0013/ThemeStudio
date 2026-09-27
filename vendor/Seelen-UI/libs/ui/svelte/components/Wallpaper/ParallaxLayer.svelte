<script lang="ts">
  import { untrack, type Snippet } from "svelte";
  import { ParallaxController } from "../../../shared/wallpaper-parallax/controller.ts";
  import type { ParallaxSettings, Rect } from "../../../shared/wallpaper-parallax/motion.ts";
  let { children, options, pointer = null, sourceBounds, paused = false, localPointer = false }:
    { children: Snippet; options: ParallaxSettings; pointer?: [number, number] | null; sourceBounds?: Rect; paused?: boolean; localPointer?: boolean } = $props();
  let controller = $state.raw<ParallaxController | null>(null);

  function attachLayer(element: HTMLElement) {
    const active = new ParallaxController(element, element.parentElement!, untrack(() => options));
    controller = active;
    return () => { active.destroy(); if (controller === active) controller = null; };
  }
  $effect(() => controller?.configure(options));
  $effect(() => controller?.setPaused(paused));
  $effect(() => {
    options; // Re-sample the current native cursor when an effect is enabled or reconfigured.
    if (pointer && sourceBounds && !paused) controller?.sample(pointer[0], pointer[1], sourceBounds);
  });
  function pointerMove(event: PointerEvent & { currentTarget: EventTarget & HTMLDivElement }) {
    if (!localPointer) return;
    const rect = event.currentTarget.getBoundingClientRect();
    controller?.sample(event.clientX, event.clientY, rect);
  }
</script>

<!-- Pointer movement only previews an effect; no activation or keyboard action. -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="parallax-viewport" onpointermove={pointerMove}>
  <div class="parallax-content" {@attach attachLayer}>{@render children()}</div>
</div>

<style>
  .parallax-viewport { position: absolute; inset: 0; overflow: hidden; }
  .parallax-content { position: absolute; top: 0; left: 0; width: 100%; height: 100%; transform-origin: 0 0; }
</style>
