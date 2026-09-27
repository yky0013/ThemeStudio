// SPDX-License-Identifier: AGPL-3.0-or-later
import type { DesktopClient } from "../../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/desktop.ts";

type Message = { id: number; result?: unknown; error?: string };
interface NativeWebView {
  postMessage(value: unknown): void;
  addEventListener(type: "message", callback: (event: MessageEvent<Message>) => void): void;
}
const native = (window as unknown as { chrome?: { webview?: NativeWebView } }).chrome?.webview;
export const isDesktopApp = !!native;
let sequence = 0;
let session = "";
const pending = new Map<number, { resolve: (value: unknown) => void; reject: (error: Error) => void }>();
native?.addEventListener("message", ({ data }) => {
  const request = pending.get(data.id);
  if (!request) return;
  pending.delete(data.id);
  if (data.error) request.reject(new Error(data.error)); else request.resolve(data.result);
});

export const studioClient: DesktopClient = {
  async call<T>(operation: string, payload = {}): Promise<T> {
    if (native) {
      const id = ++sequence;
      return await new Promise<T>((resolve, reject) => {
        pending.set(id, { resolve: (result) => resolve(result as T), reject });
        native.postMessage({ id, operation, payload });
      });
    }
    if (!session) {
      const response = await fetch("/desktop/session", { headers: { "X-Workbench-Client": "1" } });
      if (!response.ok) throw new Error("desktop_unavailable");
      session = (await response.json()).token;
    }
    const response = await fetch("/desktop/action", { method: "POST", headers: { "Content-Type": "application/json", "X-Workbench-Token": session }, body: JSON.stringify({ operation, payload }) });
    if (response.status === 403) { session = ""; throw new Error("desktop_reconnect"); }
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || response.statusText);
    return result as T;
  },
};

// The native host records readiness only after the real Windows data has rendered.
if (native) {
  const timer = setInterval(() => {
    const roles = document.querySelectorAll('#workbench-cursors button[aria-pressed]').length;
    if (roles !== 17) return;
    clearInterval(timer);
    void studioClient.call("app.ready", { roles, shortcuts: document.querySelectorAll('#workbench-desktop input[type=checkbox]').length, title: document.title });
  }, 250);
}
