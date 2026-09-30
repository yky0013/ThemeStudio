// SPDX-License-Identifier: AGPL-3.0-or-later
export interface Artwork { id: string; name: string; preview: string }
export interface Shortcut extends Artwork { origin: string; kind: string; sha256: string }
export interface CursorScheme { id: string; name: string; kind: "current" | "default" | "saved" | "factory"; size: number; roles: Record<string, string> }
export interface DesktopState {
  shortcuts: Shortcut[];
  icons: Artwork[];
  mappings?: Record<string, string>;
  administrator?: boolean;
  history: { id: string; created: string; count: number }[];
  cursors: { schemes: CursorScheme[]; resources: Record<string, { name: string; preview: string }>; roles: string[]; version: string; canRestore: boolean };
  errors: string[];
}
export interface ChangeResult { id: string; entries: { name: string; status: string; error: string }[] }
export interface CursorImport { roles: Record<string, string>; resources: DesktopState["cursors"]["resources"]; matched: number; total: number }
export interface DesktopClient { call<T>(operation: string, payload?: unknown): Promise<T> }

export function createDesktopClient(): DesktopClient {
  let token = "";
  return { async call<T>(operation: string, payload = {}) {
    if (!token) {
      const response = await fetch("/desktop/session", { headers: { "X-Workbench-Client": "1" } });
      if (!response.ok) throw new Error("desktop_unavailable");
      token = (await response.json()).token;
    }
    const response = await fetch("/desktop/action", { method: "POST", headers: { "Content-Type": "application/json", "X-Workbench-Token": token }, body: JSON.stringify({ operation, payload }) });
    if (response.status === 403) { token = ""; throw new Error("desktop_reconnect"); }
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || response.statusText);
    return result as T;
  } };
}

export async function uploadFile(file: File): Promise<{ name: string; data: string }> {
  if (!file.size || file.size > 32 * 1024 * 1024) throw new Error("file_too_large");
  return await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("read_failed"));
    reader.onload = () => resolve({ name: file.name, data: String(reader.result).split(",")[1]! });
    reader.readAsDataURL(file);
  });
}
