(async () => {
  await new Promise(resolve => setTimeout(resolve, 12000));
  const result = { title: document.title, roles: document.querySelectorAll('#workbench-cursors button[aria-pressed]').length,
    images: [...document.images].map(image => ({source: image.currentSrc.slice(0, 200), loaded: image.complete && image.naturalWidth > 0})),
    heap: performance.memory ? { used: performance.memory.usedJSHeapSize, total: performance.memory.totalJSHeapSize } : null };
  window.chrome.webview.postMessage({ id: 999001, operation: 'app.qa-complete', payload: result });
})();
