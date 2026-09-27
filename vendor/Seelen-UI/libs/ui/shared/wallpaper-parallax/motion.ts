// SPDX-License-Identifier: MIT
// Adapted from HaVeN80's Parallax Wallpaper (MIT), version 0.9.0:
// ramensoftware/windhawk-mods@682a7f72694eb768724bea8ef72b079aedd9c57b
// mods/parallax-wallpaper.wh.cpp: Preset, Normalized, AcceptInput, SpringAxis,
// Advance, Tilt, CoversViewport, PerspectiveZoom and PerspectiveMatrix.
// The original image/desktop renderer is NOT started. This port transforms the
// existing Seelen media layer, in CSS pixels. See documentation/wallpaper-parallax.md.

export const PARALLAX_THEME_ID = "@workbench/wallpaper-parallax";
export const PRESETS = {
  elegance: { x: 14, y: 8, response: 750, threshold: 0.06 },
  silk: { x: 22, y: 12, response: 1050, threshold: 0.08 },
  depth: { x: 32, y: 18, response: 850, threshold: 0.04 },
  cinema: { x: 42, y: 24, response: 1350, threshold: 0.10 },
} as const;
export type Preset = keyof typeof PRESETS;
export interface ParallaxSettings {
  enabled: boolean;
  preset: Preset;
  strength: number;
  perspective: boolean;
  tilt: number;
  opposite: boolean;
}
export const DEFAULT_PARALLAX: ParallaxSettings = {
  enabled: false, preset: "elegance", strength: 1, perspective: true, tilt: 2, opposite: true,
};
export interface Rect { left: number; top: number; right: number; bottom: number }
export interface Options { x: number; y: number; response: number; threshold: number; perspective: boolean; tilt: number; opposite: boolean }
export interface Axis { position: number; velocity: number }
export interface MotionState { x: Axis; y: Axis; tiltX: Axis; tiltY: Axis; acceptedX: number; acceptedY: number }
export interface TiltCoefficients { a: number; b: number; c: number; d: number; p: number; q: number }
const clamp = (n: number, lo: number, hi: number): number => Math.max(lo, Math.min(hi, n));

export function parseParallax(value: unknown): ParallaxSettings {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("invalid_parallax");
  const p = value as Record<string, unknown>;
  if (typeof p.enabled !== "boolean" || typeof p.perspective !== "boolean" || typeof p.opposite !== "boolean" ||
    typeof p.preset !== "string" || !Object.hasOwn(PRESETS, p.preset) ||
    typeof p.strength !== "number" || !Number.isFinite(p.strength) || p.strength < 0 || p.strength > 2 ||
    typeof p.tilt !== "number" || !Number.isFinite(p.tilt) || p.tilt < 0 || p.tilt > 8) throw new Error("invalid_parallax");
  return { enabled: p.enabled, preset: p.preset as Preset, strength: p.strength, perspective: p.perspective, tilt: p.tilt, opposite: p.opposite };
}

export function resolveOptions(settings: ParallaxSettings): Options {
  const p = PRESETS[settings.preset];
  return { ...p, x: p.x * settings.strength, y: p.y * settings.strength,
    perspective: settings.perspective, tilt: settings.tilt, opposite: settings.opposite };
}
export function toThemeVariables(s: ParallaxSettings): Record<string, string> {
  return { "--parallax-preset": s.preset, "--parallax-strength": String(s.strength),
    "--parallax-perspective": s.perspective ? "1" : "0", "--parallax-tilt": String(s.tilt), "--parallax-opposite": s.opposite ? "1" : "0" };
}
export function fromThemeVariables(enabled: boolean, values: Record<string, string> = {}): ParallaxSettings {
  const preset = values["--parallax-preset"]?.replace(/^["']|["']$/g, "") || "elegance";
  const number = (key: string, fallback: number, lo: number, hi: number): number => {
    const raw = values[key];
    const n = raw === undefined || raw.trim() === "" ? fallback : Number(raw);
    return Number.isFinite(n) ? clamp(n, lo, hi) : fallback;
  };
  return { enabled, preset: Object.hasOwn(PRESETS, preset) ? preset as Preset : "elegance",
    strength: number("--parallax-strength", 1, 0, 2), tilt: number("--parallax-tilt", 2, 0, 8),
    perspective: values["--parallax-perspective"] !== "0", opposite: values["--parallax-opposite"] !== "0" };
}
export function createMotion(): MotionState {
  return { x: { position: 0, velocity: 0 }, y: { position: 0, velocity: 0 },
    tiltX: { position: 0, velocity: 0 }, tiltY: { position: 0, velocity: 0 }, acceptedX: 0, acceptedY: 0 };
}
export function normalized(rect: Rect, x: number, y: number): [number, number] | null {
  const w = rect.right - rect.left, h = rect.bottom - rect.top;
  if (w <= 0 || h <= 0 || !Number.isFinite(x) || !Number.isFinite(y) || x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) return null;
  return [clamp(2 * (x - rect.left) / w - 1, -1, 1), clamp(2 * (y - rect.top) / h - 1, -1, 1)];
}
export function acceptInput(state: MotionState, nx: number, ny: number, threshold: number): void {
  const dx = nx - state.acceptedX, dy = ny - state.acceptedY;
  const distance = Math.hypot(dx, dy);
  if (distance > threshold) {
    const fraction = 1 - threshold / distance;
    state.acceptedX += dx * fraction;
    state.acceptedY += dy * fraction;
  }
}
export function springAxis(axis: Axis, target: number, omega: number, dt: number, limit: number): void {
  const offset = axis.position - target;
  const c = axis.velocity + omega * offset;
  const decay = Math.exp(-omega * dt);
  axis.position = target + (offset + c * dt) * decay;
  axis.velocity = (axis.velocity - omega * c * dt) * decay;
  if (axis.position < -limit || axis.position > limit) {
    axis.position = clamp(axis.position, -limit, limit); axis.velocity = 0;
  }
  if (Math.abs(axis.position - target) < 0.001 && Math.abs(axis.velocity) < 0.005) {
    axis.position = target; axis.velocity = 0;
  }
}
export function stopVelocity(state: MotionState): void {
  for (const axis of [state.x, state.y, state.tiltX, state.tiltY]) axis.velocity = 0;
}
export function advance(state: MotionState, options: Options, elapsedMs: number): boolean {
  const sign = options.opposite ? 1 : -1;
  const omega = 4.744 / (options.response / 1000);
  const dt = clamp(elapsedMs, 0, 50) / 1000;
  const targets: [Axis, number, number][] = [[state.x, sign * state.acceptedX * options.x, options.x],
    [state.y, sign * state.acceptedY * options.y, options.y],
    [state.tiltX, options.perspective ? sign * state.acceptedX : 0, 1],
    [state.tiltY, options.perspective ? sign * state.acceptedY : 0, 1]];
  for (const [axis, target, limit] of targets) springAxis(axis, target, omega, dt, limit);
  return targets.some(([axis, target]) => axis.position !== target || axis.velocity !== 0);
}

export function tiltCoefficients(width: number, height: number, tilt: number, x: number, y: number): TiltCoefficients {
  const radians = Math.PI / 180;
  const ry = x * tilt * radians, rx = -y * tilt * radians;
  const inverseDistance = 1 / (2 * Math.max(width, height));
  return { a: Math.cos(ry), b: Math.sin(rx) * Math.sin(ry), c: 0, d: Math.cos(rx),
    p: -Math.sin(ry) * inverseDistance, q: Math.sin(rx) * Math.cos(ry) * inverseDistance };
}
export function coversViewport(width: number, height: number, t: TiltCoefficients, zoom: number): boolean {
  const cx = width / 2, cy = height / 2;
  const limitX = cx - Math.min(1, cx * 0.01), limitY = cy - Math.min(1, cy * 0.01);
  for (const ix of [-1, 1]) for (const iy of [-1, 1]) {
    const u = ix * cx / zoom, v = iy * cy / zoom;
    const aa = t.a - u * t.p, bb = t.b - u * t.q, cc = t.c - v * t.p, dd = t.d - v * t.q;
    const determinant = aa * dd - bb * cc;
    if (Math.abs(determinant) < 1e-9) return false;
    const sx = (u * dd - bb * v) / determinant, sy = (aa * v - u * cc) / determinant;
    if (1 + t.p * sx + t.q * sy <= 0 || Math.abs(sx) > limitX || Math.abs(sy) > limitY) return false;
  }
  return true;
}
export function perspectiveZoom(width: number, height: number, options: Options): number {
  if (!options.perspective || options.tilt === 0 || width <= 0 || height <= 0) return 1;
  let zoom = 1;
  for (let i = -4; i <= 4; i++) for (let j = -4; j <= 4; j++) {
    const t = tiltCoefficients(width, height, options.tilt, i / 4, j / 4);
    if (coversViewport(width, height, t, zoom)) continue;
    let low = zoom, high = 8;
    for (let k = 0; k < 24; k++) {
      const mid = (low + high) / 2;
      if (coversViewport(width, height, t, mid)) high = mid; else low = mid;
    }
    zoom = high;
  }
  return zoom;
}
export function transformMatrix(width: number, height: number, state: MotionState, options: Options, zoom: number): number[] {
  const t = options.perspective ? tiltCoefficients(width, height, options.tilt, state.tiltX.position, state.tiltY.position) : { a: 1, b: 0, c: 0, d: 1, p: 0, q: 0 };
  const cx = width / 2, cy = height / 2;
  const sx = cx + options.x + state.x.position, sy = cy + options.y + state.y.position;
  const a = zoom * t.a + cx * t.p, b = zoom * t.b + cx * t.q;
  const c = zoom * t.c + cy * t.p, d = zoom * t.d + cy * t.q;
  // D2D row-vector matrix and CSS matrix3d column-major serialization have the
  // same slot ordering for this projective 2D transform (z remains zero).
  return [a, c, 0, t.p, b, d, 0, t.q, 0, 0, 1, 0,
    cx - sx * a - sy * b, cy - sx * c - sy * d, 0, 1 - sx * t.p - sy * t.q];
}
