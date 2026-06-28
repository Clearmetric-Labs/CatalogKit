import {
  loadBundle,
  loadArtifact,
  groupByKind,
  warningsForNode,
  requiredBundleParam,
  escapeHtml,
} from "../shared/artifact-kit.mjs";

const app = document.getElementById("app");
const lineageLink = document.getElementById("lineage-link");

function renderError(message) {
  app.innerHTML = `<p class="error">${escapeHtml(message)}</p>`;
}

function filterNodes(nodes, query) {
  const q = query.trim().toLowerCase();
  if (!q) return nodes;
  return nodes.filter(
    (node) =>
      node.id.toLowerCase().includes(q) ||
      node.name.toLowerCase().includes(q) ||
      node.kind.toLowerCase().includes(q),
  );
}

function renderNodeDetail(node, catalog) {
  const warnings = warningsForNode(catalog.warnings, node.id);
  return `
    <h2>${escapeHtml(node.id)}</h2>
    <p class="meta">${escapeHtml(node.kind)} · ${escapeHtml(node.name)}</p>
    <h3>Bindings</h3>
    <pre>${escapeHtml(JSON.stringify(node.bindings ?? null, null, 2))}</pre>
    <h3>Aspects</h3>
    <pre>${escapeHtml(JSON.stringify(node.aspects ?? null, null, 2))}</pre>
    <h3>Warnings</h3>
    <pre>${escapeHtml(JSON.stringify(warnings, null, 2))}</pre>
    <details>
      <summary>Raw node JSON</summary>
      <pre>${escapeHtml(JSON.stringify(node, null, 2))}</pre>
    </details>
  `;
}

function render(bundle, catalog, selectedId, searchQuery) {
  const groups = groupByKind(catalog.nodes);
  const kinds = [...groups.keys()].sort();
  const selected = catalog.nodes.find((node) => node.id === selectedId) || null;

  app.innerHTML = `
    <aside class="sidebar">
      <input class="search" type="search" placeholder="Search id, name, kind" value="${escapeHtml(searchQuery)}" />
      ${kinds
        .map((kind) => {
          const nodes = filterNodes(groups.get(kind), searchQuery);
          return `
            <h2>${escapeHtml(kind)} (${nodes.length})</h2>
            <ul>
              ${nodes
                .map(
                  (node) => `
                <li>
                  <button data-id="${escapeHtml(node.id)}" class="${node.id === selected?.id ? "active" : ""}">
                    ${escapeHtml(node.id)}
                  </button>
                </li>`,
                )
                .join("")}
            </ul>`;
        })
        .join("")}
    </aside>
    <section class="content">
      ${selected ? renderNodeDetail(selected, catalog) : "<p>Select a node</p>"}
    </section>
  `;

  const searchInput = app.querySelector(".search");
  searchInput.addEventListener("input", () => {
    render(bundle, catalog, selectedId, searchInput.value);
  });

  app.querySelectorAll("button[data-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.getAttribute("data-id");
      window.location.hash = `node=${encodeURIComponent(id)}`;
      render(bundle, catalog, id, searchInput.value);
    });
  });
}

async function main() {
  try {
    const bundleUrl = requiredBundleParam();
    lineageLink.href = `../lineage-explorer/index.html?bundle=${encodeURIComponent(bundleUrl)}`;
    const bundle = await loadBundle(bundleUrl);
    const catalog = await loadArtifact(bundle, "catalog");
    const hash = window.location.hash.replace(/^#node=/, "");
    const selectedId = hash ? decodeURIComponent(hash) : catalog.nodes[0]?.id || null;
    render(bundle, catalog, selectedId, "");
  } catch (error) {
    renderError(error.message);
  }
}

main();
