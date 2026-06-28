import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  loadBundle,
  loadArtifact,
  loadImpact,
  indexNodes,
  groupByKind,
  warningsForNode,
} from "./artifact-kit.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const minimalBase = path.resolve(here, "../bundles/minimal");

function installFileFetch(baseDir) {
  global.fetch = async (url) => {
    const relative = String(url).replace(`${baseDir}/`, "");
    const filePath = path.join(baseDir, relative);
    const body = await readFile(filePath, "utf8");
    return {
      ok: true,
      status: 200,
      json: async () => JSON.parse(body),
    };
  };
}

test("loadBundle loads minimal manifest and artifacts", async () => {
  installFileFetch(minimalBase);
  const bundle = await loadBundle(`${minimalBase}/`);
  assert.equal(bundle.manifest.scenario_id, "minimal");

  const catalog = await loadArtifact(bundle, "catalog");
  assert.ok(Array.isArray(catalog.nodes));

  const impact = await loadImpact(bundle, "orders.amount_upstream");
  assert.equal(impact.selection_id, "column:orders.amount");

  const byId = indexNodes(catalog.nodes);
  assert.ok(byId.has("column:orders.amount"));

  const groups = groupByKind(catalog.nodes);
  assert.ok(groups.has("column"));

  const warnings = warningsForNode(catalog.warnings, "column:orders.amount");
  assert.ok(Array.isArray(warnings));
});

test("loadBundle throws without baseUrl", async () => {
  await assert.rejects(() => loadBundle(""), /Missing required \?bundle=/);
});

test("admin lane envelope throws", async () => {
  installFileFetch(minimalBase);
  const bundle = await loadBundle(`${minimalBase}/`);
  global.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      format: "consumer-catalog",
      version: "1",
      identity: "analyst",
      node_count: 0,
      edge_count: 0,
      payload: { version: "1", nodes: [], edges: [], warnings: [] },
    }),
  });
  await assert.rejects(() => loadArtifact(bundle, "graph"), /must not be wrapped/);
});

test("consumer lane missing envelope throws", async () => {
  global.fetch = async (url) => {
    if (String(url).endsWith("bundle.manifest.json")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          schema_version: "1",
          scenario_id: "x",
          label: "x",
          artifacts: {
            graph: {
              path: "graph.json",
              kind: "catalog-artifact",
              lane: "consumer",
              identity: "analyst",
            },
            catalog: {
              path: "catalog.json",
              kind: "catalog-artifact",
              lane: "admin",
            },
            impacts: {
              k: { path: "i.json", selection: "x", direction: "upstream" },
            },
          },
          defaults: { impact_key: "k" },
        }),
      };
    }
    return {
      ok: true,
      status: 200,
      json: async () => ({ version: "1", nodes: [], edges: [], warnings: [] }),
    };
  };
  const bundle = await loadBundle("http://local/");
  await assert.rejects(() => loadArtifact(bundle, "graph"), /missing envelope field/);
});

test("unknown artifact key throws", async () => {
  global.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      schema_version: "1",
      scenario_id: "x",
      label: "x",
      artifacts: {
        graph: { path: "g", kind: "catalog-artifact", lane: "admin" },
        catalog: { path: "c", kind: "catalog-artifact", lane: "admin" },
        impacts: {
          k: { path: "i.json", selection: "x", direction: "upstream" },
        },
      },
      defaults: { impact_key: "k" },
    }),
  });
  const bundle = await loadBundle("http://local/");
  await assert.rejects(() => loadArtifact(bundle, "missing"), /Unknown artifact key/);
});
