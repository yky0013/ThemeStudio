(async () => {
  let sequence = 100000;
  const pending = new Map();
  const bridge = window.chrome.webview;
  bridge.addEventListener("message", ({ data }) => {
    const request = pending.get(data.id);
    if (!request) return;
    pending.delete(data.id);
    data.error ? request.reject(new Error(data.error)) : request.resolve(data.result);
  });
  const call = (operation, payload = {}) => new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, { resolve, reject });
    bridge.postMessage({ id, operation, payload });
  });
  const result = { checks: [], errors: [] };
  const settings = { enabled: true, preset: "elegance", strength: 1, perspective: true, tilt: 2, opposite: true };
  try {
    result.checks.push({ ui: document.title, roles: document.querySelectorAll('#workbench-cursors button[aria-pressed]').length, pairRows: document.querySelectorAll('#workbench-desktop select').length });
    for (const kind of ["image", "video"]) {
      const media = await call("wallpaper.example", { kind });
      const applied = await call("wallpaper.apply", { mediaId: media.id, settings });
      if (!applied.active || !applied.windows?.length || applied.windows.some((window) => !window.attached)) throw new Error("Wallpaper did not attach to the desktop layer");
      result.checks.push({ kind, mediaId: media.id, applied });
      const paused = await call("wallpaper.pause", { paused: true });
      if (!paused.paused) throw new Error("Desktop pause was not acknowledged");
      const resumed = await call("wallpaper.pause", { paused: false });
      if (resumed.paused) throw new Error("Desktop resume was not acknowledged");
      const stopped = await call("wallpaper.stop");
      if (stopped.active) throw new Error("Desktop playback did not stop");
      result.checks.push({ kind, paused: true, resumed: true, restored: true });
    }
  } catch (error) {
    result.errors.push(String(error));
    try { await call("wallpaper.stop"); } catch (cleanup) { result.errors.push(String(cleanup)); }
  }
  result.passed = result.errors.length === 0;
  await call("app.qa-complete", result);
})();
