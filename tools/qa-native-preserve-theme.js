// Native startup + preview regression. No appearance-changing action is sent.
(async () => {
  let sequence = 910000;
  const pending = new Map(), bridge = window.chrome.webview;
  bridge.addEventListener('message', ({data}) => {
    const entry = pending.get(data.id); if (!entry) return;
    pending.delete(data.id); data.error ? entry.reject(new Error(data.error)) : entry.resolve(data.result);
  });
  const call = (operation, payload = {}) => new Promise((resolve, reject) => {
    const id = ++sequence; pending.set(id, {resolve, reject}); bridge.postMessage({id, operation, payload});
  });
  const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
  const result = {checks: [], errors: []};
  try {
    await delay(1800);
    const startup = await call('app.qa-trace');
    const allowed = new Set(['state', 'runtime.state', 'templates.list', 'wallpaper.status', 'updates.state', 'app.ready', 'app.qa-trace', 'explorer.state', 'pets.state']);
    const writes = startup.filter(operation => !allowed.has(operation));
    if (writes.length) throw new Error('Startup sent modifying operations: ' + writes.join(', '));
    result.checks.push({startupReadOnly: true, operations: startup});
    const accessories = [...document.querySelectorAll('#workbench-templates input[type=checkbox]')];
    if (accessories.length !== 2 || accessories.some(input => input.checked)) throw new Error('Accessories are not opt-in');
    result.checks.push({cursorsAndIconsUnchecked: true});
    const explorer = await call('explorer.state');
    const pets = await call('pets.state');
    if (!document.getElementById('workbench-explorer') || !document.getElementById('workbench-pets')) throw new Error('New panels missing');
    if (!explorer.choices.length || pets.pets.length) throw new Error('Unexpected fresh state');
    if (![...document.querySelectorAll('#workbench-templates button')].some(button=>button.textContent.includes('导入图片'))) throw new Error('Direct media import missing');
    result.checks.push({explorerPresets:explorer.choices.length, freshPetsEmpty:true, directMediaImport:true});
    const packs = await call('templates.list');
    if (packs.packs.length < 10) throw new Error('Bundled packs missing');
    const state = await call('state');
    const factory = state.cursors.schemes.find(scheme => scheme.kind === 'factory');
    if (factory && ![...document.querySelectorAll('#workbench-cursors button')].some(button => button.textContent.includes('恢复本机天选姬'))) throw new Error('Factory restore button is missing');
    result.checks.push({factoryRestoreVisible: !!factory});
    for (const pack of packs.packs.filter(pack => pack.source === 'builtin')) {
      if (pack.animatedWallpaper) throw new Error('Bundled motion remains');
      if (pack.version !== '2.1.0') throw new Error('Old accessories pack: ' + pack.id);
      const assets = ['accessories-preview.png', 'cursor-preview.png', ...Object.keys(pack.icons).map(key => 'icons/' + key + '.ico'), ...Object.keys(pack.cursors).map(key => 'cursor-previews/' + key + '.png')];
      await Promise.all(assets.map(asset => new Promise((resolve, reject) => { const image = new Image(); image.onload = resolve; image.onerror = () => reject(new Error('Asset preview failed: ' + pack.id + '/' + asset)); image.src = '/templates/' + pack.id + '/' + asset; })));
      result.checks.push({pack: pack.id, renderedAssets: assets.length});
    }
    for (const pack of packs.packs.slice(0, 2)) {
      const preview = await call('templates.preview', {id: pack.id, wallpaperMode: 'static'});
      await new Promise((resolve, reject) => { const image = new Image(); image.onload = resolve; image.onerror = reject; image.src = preview.url; });
    }
    const previewButton = document.querySelector('#workbench-templates button[aria-label^="预览"]');
    previewButton.click(); await delay(800);
    if (!document.querySelector('[role=dialog]')) throw new Error('Preview did not open');
    const sheet = document.querySelector('[role=dialog] details img');
    if (!sheet || !sheet.complete || !sheet.naturalWidth) throw new Error('Full accessories preview failed');
    document.querySelector('button[aria-label="关闭预览"]').click();
    await call('runtime.state'); await call('state'); await call('wallpaper.status');
    const trace = await call('app.qa-trace');
    allowed.add('templates.preview');
    if (trace.some(operation => !allowed.has(operation))) throw new Error('Preview or refresh modified appearance');
    result.checks.push({previewAndRefreshReadOnly: true, operations: trace});
    document.getElementById('workbench-templates').scrollIntoView();
    await delay(250);
    if (document.documentElement.scrollWidth > innerWidth) throw new Error('Page overflows');
  } catch (error) { result.errors.push(String(error)); }
  result.passed = result.errors.length === 0;
  await call('app.qa-complete', result);
})();
