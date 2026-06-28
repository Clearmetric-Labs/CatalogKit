/**
 * Minimal loader/helpers for consumer bundle artifacts.
 * Deliberately boring — no policy, traversal, or layout logic.
 */

export function requiredBundleParam(search = window.location.search) {
  const value = new URLSearchParams(search).get("bundle");
  if (!value) {
    throw new Error("Missing required ?bundle= query parameter");
  }
  return value;
}

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export async function loadJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: HTTP ${response.status}`);
  }
  try {
    return await response.json();
  } catch (error) {
    throw new Error(`Invalid JSON at ${url}: ${error.message}`);
  }
}

function requireManifestFields(manifest) {
  const required = ["schema_version", "scenario_id", "label", "artifacts", "defaults"];
  for (const field of required) {
    if (!(field in manifest)) {
      throw new Error(`bundle.manifest.json missing required field: ${field}`);
    }
  }
  if (!manifest.artifacts?.graph || !manifest.artifacts?.catalog || !manifest.artifacts?.impacts) {
    throw new Error("bundle.manifest.json artifacts must include graph, catalog, and impacts");
  }
  const impactKey = manifest.defaults?.impact_key;
  if (!impactKey) {
    throw new Error("bundle.manifest.json missing defaults.impact_key");
  }
  if (!(impactKey in manifest.artifacts.impacts)) {
    throw new Error(
      `defaults.impact_key ${impactKey} not found in artifacts.impacts`,
    );
  }
}

export async function loadBundle(baseUrl) {
  if (!baseUrl?.trim()) {
    throw new Error("Missing required ?bundle= query parameter");
  }
  const normalized = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
  const manifest = await loadJson(`${normalized}bundle.manifest.json`);
  requireManifestFields(manifest);
  return { baseUrl: normalized, manifest };
}

function unwrapArtifact(data, lane) {
  if (lane === "admin") {
    if ("format" in data && "payload" in data) {
      throw new Error("Admin lane artifact must not be wrapped in consumer envelope");
    }
    return data;
  }
  if (lane === "consumer") {
    for (const field of ["format", "version", "identity", "node_count", "edge_count", "payload"]) {
      if (!(field in data)) {
        throw new Error(`Consumer lane artifact missing envelope field: ${field}`);
      }
    }
    return data.payload;
  }
  throw new Error(`Unsupported lane: ${lane}`);
}

export async function loadArtifact(bundle, artifactKey) {
  const ref = bundle.manifest.artifacts[artifactKey];
  if (!ref) {
    throw new Error(`Unknown artifact key: ${artifactKey}`);
  }
  const data = await loadJson(`${bundle.baseUrl}${ref.path}`);
  return unwrapArtifact(data, ref.lane);
}

export async function loadImpact(bundle, impactKey) {
  const ref = bundle.manifest.artifacts.impacts[impactKey];
  if (!ref) {
    throw new Error(`Unknown impact key: ${impactKey}`);
  }
  return loadJson(`${bundle.baseUrl}${ref.path}`);
}

export function indexNodes(nodes) {
  return new Map(nodes.map((node) => [node.id, node]));
}

export function groupByKind(nodes) {
  const groups = new Map();
  for (const node of nodes) {
    const list = groups.get(node.kind) || [];
    list.push(node);
    groups.set(node.kind, list);
  }
  for (const list of groups.values()) {
    list.sort((a, b) => a.id.localeCompare(b.id));
  }
  return groups;
}

export function warningsForNode(warnings, nodeId) {
  return (warnings || []).filter(
    (warning) => warning.subject_id === nodeId || warning.subject_id == null,
  );
}
