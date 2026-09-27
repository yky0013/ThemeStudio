(async () => {
  let sequence = 300000;
  const pending = new Map();
  const bridge = window.chrome.webview;
  bridge.addEventListener("message", ({ data }) => { const item = pending.get(data.id); if (!item) return; pending.delete(data.id); data.error ? item.reject(new Error(data.error)) : item.resolve(data.result); });
  const call = (operation, payload = {}) => new Promise((resolve, reject) => { const id = ++sequence; pending.set(id, { resolve, reject }); bridge.postMessage({ id, operation, payload }); });
  const report = { passed: false, errors: [], checks: [] };
  try {
    const state = await call("state");
    if (!state.administrator) throw new Error("Production application did not inherit administrator authorization");
    const target = state.shortcuts.find((item) => item.name.startsWith("ThemeStudio 权限验证"));
    if (!target || !state.icons.length) throw new Error("Isolated public-desktop fixture is missing");
    const applied = await call("icons.apply", { items: [{ ...target, icon: state.icons[0].id }] });
    if (applied.entries[0]?.status !== "applied") throw new Error("Administrator public-desktop write failed: " + JSON.stringify(applied));
    const restored = await call("icons.restore", { id: applied.id });
    if (restored.entries[0]?.status !== "restored") throw new Error("Public-desktop restore failed");
    report.checks.push({ administrator: true, publicDesktopApplied: applied, publicDesktopRestored: restored });
    const seelen = await call("runtime.seelen.apply", { seelen: { activeThemes: ["@default/theme", "@eythaann/bubbles"], activeIconPacks: ["@system/icon-pack"] } });
    if (!seelen.running || !seelen.dock || !seelen.toolbar) throw new Error("Dock and toolbar were not acknowledged by the running engine");
    report.checks.push({ seelen });
    const stopped = await call("runtime.seelen.stop");
    if (stopped.dock || stopped.toolbar) throw new Error("Dock and toolbar did not stop");
    report.checks.push({ seelenStopped: stopped });
    report.passed = true;
  } catch (error) {
    report.errors.push(String(error));
    try { await call("runtime.seelen.stop"); } catch (cleanup) { report.errors.push(String(cleanup)); }
  }
  await call("app.qa-complete", report);
})();
