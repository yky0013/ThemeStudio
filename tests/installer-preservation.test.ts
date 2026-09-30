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
