import test from "node:test";
import assert from "node:assert/strict";
import { authorizedDesktopRequest, operations, sessionToken } from "../tools/desktop-host.ts";

test("desktop writes require POST, JSON and the current private session token", () => {
  const request = { method: "POST", headers: { "x-workbench-token": sessionToken, "content-type": "application/json" } };
  assert.equal(authorizedDesktopRequest(request), true);
  assert.equal(authorizedDesktopRequest({ ...request, method: "GET" }), false);
  assert.equal(authorizedDesktopRequest({ ...request, headers: { "content-type": "application/json" } }), false);
  assert.equal(authorizedDesktopRequest({ ...request, headers: { ...request.headers, "content-type": "text/plain" } }), false);
  assert.equal(authorizedDesktopRequest({ ...request, headers: { ...request.headers, "sec-fetch-site": "cross-site" } }), false);
});

test("desktop host permits only scoped personalization operations", () => {
  assert.equal(operations.has("icons.apply"), true);
  assert.equal(operations.has("cursors.restore"), true);
  assert.equal(operations.has("exec"), false);
  assert.equal(operations.has("readFile"), false);
});
