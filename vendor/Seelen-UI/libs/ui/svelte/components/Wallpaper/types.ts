import type { Wallpaper, WallpaperInstanceSettings } from "@seelen-ui/lib/types";

export interface BaseProps {
  definition?: Wallpaper;
  config?: WallpaperInstanceSettings;
  onLoad?: () => void;
  out?: boolean;

  muted?: boolean;
  paused?: boolean;
  pausedMessage?: string;
  /** Use the thumbnail of the wallpaper instead of the video */
  static?: boolean;
}

export interface DefinedWallProps extends BaseProps {
  definition: Wallpaper;
  config: WallpaperInstanceSettings;
  /** Explicit in-memory URL used by the local media preview; no Tauri path conversion. */
  sourceOverride?: string;
  /** Optional preview error feedback; existing wallpaper recovery stays intact. */
  onError?: () => void;
}
