import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const script = fs.readFileSync(new URL('../installer/ThemeStudio.iss', import.meta.url), 'utf8');
const sections = (name: string) => script.split(`[${name}]`)[1]?.split(/\r?\n\[/)[0] ?? '';

test('install and upgrade have no automatic desktop engine lifecycle action', () => {
  const entries = sections('Run').split(/\r?\n/).filter(line => line.startsWith('Filename:'));
  assert.ok(entries.every(line => line.includes('help\\index.html') && /\bunchecked\b/.test(line)));
  assert.match(script, /^CloseApplications=no$/m);
  assert.match(script, /^RestartApplications=no$/m);
  assert.equal(sections('Registry').trim(), '');
});

test('installer only consumes explicit application payload directories', () => {
  const files = sections('Files');
  assert.ok(!files.includes('ThemeStudio-{#AppVersion}\\*"'));
  assert.ok(!files.includes('Diagnostic'));
  assert.ok(!files.includes('{localappdata}') && !files.includes('{userappdata}'));
  for (const name of ['backend', 'wwwroot', 'resources', 'runtimes', 'licenses', 'docs']) {
    assert.ok(files.includes(`\\${name}\\*"`));
  }
});

test('trial installs alongside mainline with independent identity and profile', () => {
  assert.ok(!script.includes('34717904-40BD-47C3-9AE5-4CA3B55820B5'));
  assert.match(script, /DefaultDirName=\{autopf\}\\ThemeStudio-NoSeelen/);
  assert.match(script, /AppMutex=Local\\ThemeStudio\.NoSeelen\.Application/);
  const host = fs.readFileSync(new URL('../src/host/ThemeStudio.cs', import.meta.url), 'utf8');
  assert.ok(host.includes('LocalApplicationData), "ThemeStudio-NoSeelen"'));
  const runtime = JSON.parse(fs.readFileSync(new URL('../config/runtime-distributions.json', import.meta.url), 'utf8'));
  assert.ok(runtime.windhawk && !runtime.seelen);
  const packaging = fs.readFileSync(new URL('../tools/package.ps1', import.meta.url), 'utf8');
  assert.ok(!packaging.includes('seelen-engine') && !packaging.includes('seelen-themes'));
});
