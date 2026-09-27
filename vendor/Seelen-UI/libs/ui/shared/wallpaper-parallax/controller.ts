import { acceptInput, advance, createMotion, normalized, perspectiveZoom, resolveOptions, stopVelocity, transformMatrix } from "./motion.ts";
import type { ParallaxSettings, Rect } from "./motion.ts";

/** Owns only the transform layer. Never replaces or seeks the existing video. */
export class ParallaxController {
  private state = createMotion();
  private options;
  private width = 0;
  private height = 0;
  private zoom = 1;
  private frame: number | null = null;
  private lastTime = 0;
  private paused = false;
  private disposed = false;
  private resize: ResizeObserver;
  private visibility = (): void => { this.suspend(); if (!document.hidden) this.wake(); };

  constructor(private layer: HTMLElement, private viewport: HTMLElement, private settings: ParallaxSettings) {
    this.options = resolveOptions(settings);
    this.resize = new ResizeObserver(() => this.measure());
    this.resize.observe(viewport);
    document.addEventListener("visibilitychange", this.visibility);
    this.measure();
  }
  configure(settings: ParallaxSettings): void {
    if (JSON.stringify(settings) === JSON.stringify(this.settings)) return;
    this.settings = settings;
    this.options = resolveOptions(settings);
    this.state = createMotion();
    this.measure();
  }
  setPaused(paused: boolean): void {
    if (paused === this.paused) return;
    this.paused = paused;
    if (paused) this.suspend(); else this.wake();
  }
  sample(x: number, y: number, sourceBounds: Rect): void {
    if (this.disposed || this.paused || document.hidden || !this.settings.enabled) return;
    const point = normalized(sourceBounds, x, y);
    if (!point) return;
    const previousX = this.state.acceptedX, previousY = this.state.acceptedY;
    acceptInput(this.state, point[0], point[1], this.options.threshold);
    if (previousX !== this.state.acceptedX || previousY !== this.state.acceptedY) this.wake();
  }
  private measure(): void {
    if (this.disposed) return;
    this.width = this.viewport.clientWidth;
    this.height = this.viewport.clientHeight;
    this.zoom = perspectiveZoom(this.width, this.height, this.options);
    this.paint();
    this.wake();
  }
  private paint(): void {
    if (!this.settings.enabled || this.width <= 0 || this.height <= 0) {
      this.layer.style.width = "100%"; this.layer.style.height = "100%";
      this.layer.style.transform = "none"; this.layer.style.willChange = "auto";
      this.layer.dataset.parallaxActive = "false";
      return;
    }
    this.layer.style.width = `${this.width + 2 * this.options.x}px`;
    this.layer.style.height = `${this.height + 2 * this.options.y}px`;
    this.layer.style.transformOrigin = "0 0";
    this.layer.style.willChange = "transform";
    this.layer.style.transform = `matrix3d(${transformMatrix(this.width, this.height, this.state, this.options, this.zoom).join(",")})`;
    this.layer.dataset.parallaxActive = "true";
  }
  private wake(): void {
    if (this.disposed || this.paused || document.hidden || !this.settings.enabled || this.frame !== null) return;
    this.lastTime = performance.now();
    this.frame = requestAnimationFrame(this.tick);
  }
  private tick = (time: number): void => {
    this.frame = null;
    if (this.disposed || this.paused || document.hidden || !this.settings.enabled) return;
    const moving = advance(this.state, this.options, time - this.lastTime);
    this.lastTime = time;
    this.paint();
    if (moving) this.frame = requestAnimationFrame(this.tick);
  };
  private suspend(): void {
    if (this.frame !== null) cancelAnimationFrame(this.frame);
    this.frame = null;
    stopVelocity(this.state);
  }
  destroy(): void {
    this.disposed = true;
    this.suspend();
    this.resize.disconnect();
    document.removeEventListener("visibilitychange", this.visibility);
    this.layer.style.transform = "none";
    this.layer.style.willChange = "auto";
    this.layer.style.width = "100%"; this.layer.style.height = "100%";
    this.layer.dataset.parallaxActive = "false";
  }
}
