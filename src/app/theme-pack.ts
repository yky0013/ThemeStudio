// SPDX-License-Identifier: AGPL-3.0-or-later
export interface ThemePack {
  id: string; name: string; subtitle: string; accent: string; pale: string;
  wallpaper: string; animatedWallpaper?: string; motionLabel?: string; thumbnail: string;
  artwork?: string; author?: string; version: string; source: 'builtin' | 'imported'; assetBase: string;
  icons: Record<string, { file: string; matches: string[] }>;
  cursors: Record<string, string>; cursorPreview?: string;
}

export const packAsset = (pack: ThemePack, path: string) => pack.assetBase + path.split('/').map(encodeURIComponent).join('/');
export const packMode = (pack: ThemePack, requested: 'static' | 'animated') => requested === 'animated' && pack.animatedWallpaper ? 'animated' : 'static';

export function bundledPack(item: ThemePack & { iconMatches: Record<string, string[]> }): ThemePack {
  return { ...item, source: 'builtin', version: '1.0.0', assetBase: '/templates/',
    icons: Object.fromEntries(Object.entries(item.iconMatches).map(([key, matches]) => [key, { file: `${item.id}/icons/${key}.ico`, matches }])),
    cursors: Object.fromEntries(['Arrow','Help','AppStarting','Wait','Crosshair','IBeam','NWPen','No','SizeNS','SizeWE','SizeNWSE','SizeNESW','SizeAll','UpArrow','Hand','Person','Pin'].map(role => [role, `${item.id}/cursors/${role}.cur`])),
    cursorPreview: `${item.id}/cursor-preview.png` };
}
