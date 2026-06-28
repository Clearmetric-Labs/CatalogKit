import {
  loadBundle,
  loadImpact,
  requiredBundleParam,
  escapeHtml,
} from "../shared/artifact-kit.mjs";

const app = document.getElementById("app");
const catalogLink = document.getElementById("catalog-link");

function renderError(message) {
  app.innerHTML = `<p class="error">${escapeHtml(message)}</p>`;
}

function renderImpact(bundle, manifest, impactKey, impact) {
  const bundleParamEncoded = encodeURIComponent(bundle.baseUrl);
  app.innerHTML = `
    <section class="content">
      <label>
        Impact
        <select class="impact-select" id="impact-select"></select>
      </label>
      <h2>${escapeHtml(impact.selection_id)}</h2>
      <p class="meta">selection: ${escapeHtml(impact.selection)} · direction: ${escapeHtml(
        manifest.artifacts.impacts[impactKey].direction,
      )}</p>
      <h3>Related IDs (${impact.related_ids.length})</h3>
      <ul class="related-list">
        ${impact.related_ids
          .map(
            (id) =>
              `<li><a href="../catalog-viewer/index.html?bundle=${bundleParamEncoded}#node=${encodeURIComponent(id)}">${escapeHtml(id)}</a></li>`,
          )
          .join("")}
      </ul>
      <h3>Derivation</h3>
      <pre>${escapeHtml(JSON.stringify(impact.derivation, null, 2))}</pre>
      <h3>Warnings</h3>
      <pre>${escapeHtml(JSON.stringify(impact.warnings, null, 2))}</pre>
    </section>
  `;

  const select = document.getElementById("impact-select");
  for (const key of Object.keys(manifest.artifacts.impacts)) {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = key;
    option.selected = key === impactKey;
    select.appendChild(option);
  }
  select.addEventListener("change", async () => {
    const next = await loadImpact(bundle, select.value);
    renderImpact(bundle, manifest, select.value, next);
  });
}

async function main() {
  try {
    const bundleUrl = requiredBundleParam();
    catalogLink.href = `../catalog-viewer/index.html?bundle=${encodeURIComponent(bundleUrl)}`;
    const bundle = await loadBundle(bundleUrl);
    const impactKey = bundle.manifest.defaults.impact_key;
    const impact = await loadImpact(bundle, impactKey);
    renderImpact(bundle, bundle.manifest, impactKey, impact);
  } catch (error) {
    renderError(error.message);
  }
}

main();
