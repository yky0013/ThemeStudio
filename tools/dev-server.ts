import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";
import { parseRecipe } from "../vendor/Seelen-UI/src/ui/react/settings/modules/themeWorkbench/domain/model.ts";
import { DesktopHost, sessionToken, authorizedDesktopRequest } from "./desktop-host.ts";

const directory = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(directory, "../dist");
const port = Number(process.env.THEME_WORKBENCH_PORT || 4327);
const desktopHost = new DesktopHost();
const mime: Record<string, string> = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml", ".mp4": "video/mp4" };
const server = http.createServer(async (request, response) => {
  try {
    if (request.headers.host !== `127.0.0.1:${port}` ||
      (request.headers.origin && request.headers.origin !== `http://127.0.0.1:${port}`)) {
      response.writeHead(403); response.end("Forbidden origin"); return;
    }
    const url = new URL(request.url || "/", "http://127.0.0.1");
    if (url.pathname === "/desktop/session" && request.method === "GET") {
      if (request.headers["x-workbench-client"] !== "1" || request.headers["sec-fetch-site"] === "cross-site") {
        response.writeHead(403); response.end("Forbidden client"); return;
      }
      response.writeHead(200, { "Content-Type": "application/json", "Cache-Control": "no-store" });
      response.end(JSON.stringify({ token: sessionToken })); return;
    }
    if (url.pathname === "/desktop/action") {
      if (!authorizedDesktopRequest(request)) { response.writeHead(403); response.end("Forbidden client"); return; }
      const chunks: Buffer[] = [];
      let size = 0;
      for await (const chunk of request) {
        const data = Buffer.from(chunk);
        size += data.length;
        if (size > 48 * 1024 * 1024) throw new Error("文件总大小超过限制。请分批导入。");
        chunks.push(data);
      }
      const { operation, payload } = JSON.parse(Buffer.concat(chunks).toString("utf8"));
      const result = await desktopHost.call(operation, payload);
      response.writeHead(200, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
      response.end(JSON.stringify(result)); return;
    }
    if (url.pathname === "/export" && request.method === "POST") {
      const chunks: Buffer[] = [];
      let size = 0;
      for await (const chunk of request) {
        const data = Buffer.from(chunk);
        size += data.length;
        if (size > 1024 * 1024) throw new Error("recipe_too_large");
        chunks.push(data);
      }
      const text = Buffer.concat(chunks).toString("utf8");
      const recipe = parseRecipe(text);
      const exportsRoot = path.join(directory, "exports");
      fs.mkdirSync(exportsRoot, { recursive: true });
      const filename = recipe.name.replace(/[^\p{L}\p{N}_-]/gu, "_").slice(0, 80) + "-" + randomUUID().slice(0, 8) + ".theme.json";
      const output = path.join(exportsRoot, filename);
      fs.writeFileSync(output, JSON.stringify(recipe, null, 2), { encoding: "utf8", flag: "wx" });
      response.writeHead(201, { "Content-Type": "application/json; charset=utf-8" });
      response.end(JSON.stringify({ path: output })); return;
    }
    if (request.method !== "GET" && request.method !== "HEAD") { response.writeHead(405); response.end("Method not allowed"); return; }
    if (url.pathname === "/health") { response.writeHead(200, { "Content-Type": "application/json" }); response.end('{"app":"theme-studio","mode":"development","desktopBridge":1}'); return; }
    const file = path.resolve(root, "." + decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname));
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { response.writeHead(404); response.end("Not found"); return; }
    const size = fs.statSync(file).size;
    const headers = { "Content-Type": mime[path.extname(file)] || "application/octet-stream", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Accept-Ranges": "bytes" };
    if (request.headers.range) {
      const match = /^bytes=(\d*)-(\d*)$/.exec(request.headers.range);
      const start = match?.[1] ? Number(match[1]) : Math.max(0, size - Number(match?.[2]));
      const end = match?.[1] && match?.[2] ? Math.min(size - 1, Number(match[2])) : size - 1;
      if (!match || start >= size || start < 0 || end < start || !Number.isFinite(start)) {
        response.writeHead(416, { "Content-Range": `bytes */${size}` }); response.end(); return;
      }
      response.writeHead(206, { ...headers, "Content-Range": `bytes ${start}-${end}/${size}`, "Content-Length": end - start + 1 });
      if (request.method === "HEAD") response.end(); else fs.createReadStream(file, { start, end }).pipe(response);
    } else {
      response.writeHead(200, { ...headers, "Content-Length": size });
      if (request.method === "HEAD") response.end(); else fs.createReadStream(file).pipe(response);
    }
  } catch (error) { response.writeHead(400, { "Content-Type": "application/json" }); response.end(JSON.stringify({ error: String(error) })); }
});
server.on("error", (error) => { console.error(error); process.exitCode = 1; });
server.on("close", () => desktopHost.close());
server.listen(port, "127.0.0.1", () => console.log(`Theme Studio: http://127.0.0.1:${port}`));
