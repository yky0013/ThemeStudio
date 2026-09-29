import assert from 'node:assert/strict';
import test from 'node:test';
import { packAsset, packMode, type ThemePack } from '../src/app/theme-pack.ts';

test('an imported static-only pack never tries to apply a missing video', () => {
  const pack = { assetBase:'https://packs.theme-studio.invalid/abc/' } as ThemePack;
  assert.equal(packMode(pack,'animated'),'static');
  assert.equal(packAsset(pack,'素材/壁纸 #1.jpg'),'https://packs.theme-studio.invalid/abc/%E7%B4%A0%E6%9D%90/%E5%A3%81%E7%BA%B8%20%231.jpg');
  assert.equal(packMode({...pack,animatedWallpaper:'motion.mp4'},'animated'),'animated');
  assert.equal(packMode({...pack,animatedWallpaper:'motion.mp4'},'static'),'static');
});
