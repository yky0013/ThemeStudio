// Private stdio connection to the existing Windows implementation.
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { createInterface } from "node:readline";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { randomBytes } from "node:crypto";
import type { IncomingMessage } from "node:http";

export const operations = new Set(["state", "icons.import", "icons.assign", "icons.apply", "icons.restore", "cursors.import", "cursors.apply", "cursors.save", "cursors.restore", "cursors.factory", "recipe.export", "runtime.state", "runtime.apply", "runtime.seelen.apply", "runtime.seelen.stop", "runtime.windhawk.apply", "runtime.windhawk.stop"]);
export const sessionToken = randomBytes(32).toString("hex");
operations.add('runtime.desktop.apply');
// Browser development can read the library; native file pickers and updater
// installer handoff are deliberately available only in the Windows host.
operations.add('templates.list');
export function authorizedDesktopRequest(request: Pick<IncomingMessage, "headers" | "method">): boolean {
  return request.method === "POST" && request.headers["x-workbench-token"] === sessionToken &&
    request.headers["content-type"]?.split(";")[0] === "application/json" &&
    request.headers["sec-fetch-site"] !== "cross-site";
}

export class DesktopHost {
  private child?: ChildProcessWithoutNullStreams;
  private pending?: { resolve: (value: unknown) => void; reject: (error: Error) => void; id: number };
  private sequence = 0;
  private start() {
    if (this.child) return;
    const workspace = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
    const python = path.join(workspace, ".venv/Scripts/python.exe");
    const script = path.join(workspace, "components/icon-workbench/desktop_bridge.py");
    if (!fs.existsSync(python) || !fs.existsSync(script)) throw new Error("桌面组件不可用，请准备当前项目的运行环境。");
    // Test launchers may isolate fixtures and backups. These paths are never accepted from HTTP.
    const args = ["-X", "utf8", "-u", script];
    if (process.env.THEME_WORKBENCH_DATA_DIR) args.push("--data-dir", process.env.THEME_WORKBENCH_DATA_DIR);
    if (process.env.THEME_WORKBENCH_SCAN_DIR) args.push("--scan-dir", process.env.THEME_WORKBENCH_SCAN_DIR);
    const child = spawn(python, args, { cwd: workspace, windowsHide: true, stdio: "pipe" });
    this.child = child;
    let errorOutput = "";
    child.stderr.on("data", (data) => { errorOutput = (errorOutput + String(data)).slice(-2048); });
    const fail = (error: Error) => { this.pending?.reject(error); this.pending = undefined; };
    child.on("error", fail);
    child.on("exit", () => { if (this.child === child) this.child = undefined; fail(new Error(errorOutput || "桌面组件已停止，请刷新后重试。")); });
    createInterface({ input: child.stdout }).on("line", (line) => {
      try {
        const result = JSON.parse(line);
        if (result.event) return;
        if (result.id !== this.pending?.id) return;
        const pending = this.pending!;
        this.pending = undefined;
        if (result.error) pending.reject(new Error(result.error)); else pending.resolve(result.result);
      } catch { fail(new Error("桌面组件返回了无效结果。")); }
    });
  }
  async call(operation: string, payload: unknown) {
    if (!operations.has(operation)) throw new Error("Unsupported desktop operation");
    if (this.pending) throw new Error("正在处理桌面操作，请稍后再试。");
    this.start();
    const id = ++this.sequence;
    return await new Promise((resolve, reject) => {
      this.pending = { resolve, reject, id };
      this.child!.stdin.write(JSON.stringify({ id, operation, payload }) + "\n", (error) => {
        if (error && this.pending?.id === id) { this.pending = undefined; reject(error); }
      });
    });
  }
  close() { this.child?.stdin.end(); }
}
