import { WallpaperConfiguration } from "@seelen-ui/lib";
export { getPlaybackRate, getWallpaperStyles } from "./appearance.ts";

export const defaultWallpaperConfig = await WallpaperConfiguration.default();
