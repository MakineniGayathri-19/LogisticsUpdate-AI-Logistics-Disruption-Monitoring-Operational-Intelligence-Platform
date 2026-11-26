const API = "/api";
const PAGE_TITLES = {
  overview: "Command center",
  forecast: "24h risk forecast",
  disruptions: "Live disruptions",
  collection: "Data collection",
  history: "Historical memory",
  comparison: "Event comparison",
  reports: "Operational reports",
  settings: "System status",
};
const CATEGORIES = [
  "Port Disruption", "Weather Disruption", "Shipping Delay",
  "Road Transportation Disruption", "Railway Disruption",
  "Carrier Announcement", "Supply Chain Disruption", "Other",
];
let currentPage = "overview";
let latestReport = null;
let cachedDisruptions = [];
let cachedStats = {};
let toastTimer;

const $ = (selector, root = document) => root.querySelector(selector);
const escapeHTML = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[char]));
const safeURL = (value) => {
  try {
    const url = new URL(value, window.location.origin);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "";
  } catch {
    return "";
  }
};
const dateText = (value) => {
  if (!value) return "Not recorded";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value).slice(0, 19) : date.toLocaleString();
};
const severity = (value) => {
  const normalized = String(value || "Unknown").toLowerCase();
  return `<span class="severity-pill ${escapeHTML(normalized)}">${escapeHTML(value || "Unknown")}</span>`;
};
const categoryOptions = (selected = "") => CATEGORIES.map((category) =>
  `<option value="${escapeHTML(category)}" ${selected === category ? "selected" : ""}>${escapeHTML(category)}</option>`
).join("");
const eventOptions = (selected = "") => cachedDisruptions.map((event) =>
  `<option value="${escapeHTML(event.id)}" ${event.id === selected ? "selected" : ""}>[${escapeHTML(event.severity)}] ${escapeHTML(event.title)} · ${escapeHTML(event.location || "Unspecified")}</option>`
).join("");

async function api(path, options = {}) {
  const response = await fetch(`${API}/${path}`, {
    ...options,
    headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers },
  });
  if (!response.ok) {
    const body = await response.text();
    let detail = body;
    try { detail = JSON.parse(body).detail || body; } catch { /* use response text */ }
    throw new Error(`Request failed (${response.status}): ${detail.slice(0, 240)}`);
  }
  return response.status === 204 ? null : response.json();
}
const post = (path, body = undefined) => api(path, { method: "POST", ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
const remove = (path) => api(path, { method: "DELETE" });

function toast(message, type = "success") {
  const region = $("#toast-region");
  region.innerHTML = `<div class="toast ${type}">${escapeHTML(message)}</div>`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { region.innerHTML = ""; }, 4800);
}
function setBusy(button, busy, label = "Working…") {
  if (!button) return;
  if (busy) {
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = `<span class="spinner"></span>${label}`;
    button.disabled = true;
  } else {
    button.innerHTML = button.dataset.originalText || button.innerHTML;
    button.disabled = false;
  }
}
function pageHeading(eyebrow, title, description, actions = "") {
  return `<div class="page-heading"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${description}</p></div><div class="heading-actions">${actions}</div></div>`;
}
function empty(message) { return `<div class="empty-state">${escapeHTML(message)}</div>`; }
function severityClass(value) {
  const val = String(value || "").toLowerCase();
  return ["critical", "high", "medium", "low"].includes(val) ? val : "unknown";
}
function eventRow(event) {
  const url = safeURL(event.source_url);
  return `<div class="event-row">
    <span class="event-accent ${severityClass(event.severity)}"></span>
    <div><a class="event-title" href="#/disruptions">${escapeHTML(event.title || "Untitled disruption")}</a>
      <div class="event-meta">${escapeHTML(event.location || "Unspecified")} · ${escapeHTML(event.category || "Other")} · ${dateText(event.collected_at)}</div>
    </div>${severity(event.severity)}
  </div>`;
}
function barChart(counts, type = "") {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return empty("No records to visualize yet.");
  const max = Math.max(...entries.map(([, count]) => Number(count)), 1);
  return `<div class="chart-list">${entries.slice(0, 7).map(([label, count]) => {
    const colorClass = type ? `severity-${severityClass(label)}` : "";
    return `<div class="chart-row"><span>${escapeHTML(label || "Unspecified")}</span><div class="chart-track"><div class="chart-bar ${colorClass}" style="width:${Math.max(3, Number(count) / max * 100)}%"></div></div><span class="chart-count">${Number(count)}</span></div>`;
  }).join("")}</div>`;
}

async function loadCommon() {
  const [disruptions, stats] = await Promise.all([
    api("disruptions"),
    api("stats"),
  ]);
  cachedDisruptions = disruptions;
  cachedStats = stats;
  $("#nav-disruption-count").textContent = String(disruptions.length);
}

async function renderOverview() {
  await loadCommon();
  const [reports, history, logs] = await Promise.all([
    api("reports"), api("historical-events"), api("logs?limit=6"),
  ]);
  const critical = cachedDisruptions.filter((item) => String(item.severity).toLowerCase() === "critical").length;
  const high = cachedDisruptions.filter((item) => String(item.severity).toLowerCase() === "high").length;
  const active = cachedDisruptions.filter((item) => String(item.status).toLowerCase() === "active").length;
  const categories = {};
  const severities = {};
  cachedDisruptions.forEach((item) => {
    const category = item.category || "Other";
    const level = item.severity || "Unknown";
    categories[category] = (categories[category] || 0) + 1;
    severities[level] = (severities[level] || 0) + 1;
  });
  const priorities = [...cachedDisruptions].sort((a, b) => {
    const order = { critical: 4, high: 3, medium: 2, low: 1 };
    return (order[String(b.severity).toLowerCase()] || 0) - (order[String(a.severity).toLowerCase()] || 0);
  }).filter((item) => ["critical", "high"].includes(String(item.severity).toLowerCase())).slice(0, 5);
  const lastCollection = cachedStats.last_collection_time || "No successful collection recorded";
  $("#page-content").innerHTML = `
    <section class="hero">
      <div class="hero-content"><div class="eyebrow">GLOBAL OPERATIONS · LIVE INTELLIGENCE</div>
        <h1>See the signal.<br>Stay ahead of disruption.</h1>
        <p>One clear view of network risk, emerging incidents, and operational context across your logistics landscape.</p>
        <div class="heading-actions"><a class="btn btn-primary" href="#/disruptions">Explore live disruptions <span class="icon-inline">→</span></a><button class="btn" data-action="collect"><span class="icon-inline">↻</span> Run collection</button></div>
      </div><div class="hero-graphic"><div class="radar"></div><i class="radar-dot one"></i><i class="radar-dot two"></i></div>
    </section>
    <div class="stats-grid">
      ${statCard("Total disruptions", cachedStats.total_disruptions ?? cachedDisruptions.length, "Across monitored feeds", "↗")}
      ${statCard("Active incidents", cachedStats.active_disruptions ?? active, `${critical} critical · ${high} high priority`, "!")}
      ${statCard("Historical precedents", cachedStats.historical_stored ?? history.length, "Available for comparison", "◷")}
      ${statCard("Reports generated", cachedStats.ai_reports_generated ?? reports.length, "Operational reports in archive", "▤")}
    </div>
    <div class="section-title"><h2>Network intelligence</h2><span>Latest system snapshot</span></div>
    <div class="dashboard-grid">
      <section class="panel"><div class="panel-heading"><div><h3>Disruptions by category</h3><p>Incident mix across your monitored network</p></div><span class="tag">${cachedDisruptions.length} events</span></div>${barChart(categories)}</section>
      <section class="panel"><div class="panel-heading"><div><h3>Severity distribution</h3><p>Current priority profile</p></div></div>${barChart(severities, "severity")}</section>
      <section class="panel"><div class="panel-heading"><div><h3>Priority watchlist</h3><p>High-impact events that may need attention</p></div><a class="btn btn-small" href="#/disruptions">View all →</a></div>
        <div class="event-list">${priorities.length ? priorities.map(eventRow).join("") : empty("No high-priority incidents in the current feed.")}</div>
      </section>
      <section class="panel"><div class="panel-heading"><div><h3>Collection activity</h3><p>Last successful run · ${escapeHTML(dateText(lastCollection))}</p></div><a class="btn btn-small" href="#/collection">Open pipeline →</a></div>
        ${logs.length ? `<div class="table-wrap"><table><thead><tr><th>Feed</th><th>Status</th><th>Records</th><th>Run time</th></tr></thead><tbody>${logs.slice(0, 5).map((log) => `<tr><td>${escapeHTML(log.source_url || "—")}</td><td>${escapeHTML(log.status || "—")}</td><td>${Number(log.records_count || 0)}</td><td>${escapeHTML(dateText(log.created_at))}</td></tr>`).join("")}</tbody></table></div>` : empty("Collection runs will appear here after the first pipeline execution.")}
      </section>
    </div>`;
}
async function renderForecast() {
  const forecast = await api("forecast");
  $("#page-content").innerHTML = `
    ${pageHeading("Live public weather data", "24-hour hub risk forecast.", "A transparent weather-exposure index for major logistics hubs, calculated from the next 24 hours of live hourly forecasts.")}
    <div class="notice"><strong>This is a rule-based weather risk index, not a trained probability model.</strong> It uses live Open-Meteo forecasts for wind, gusts, precipitation, snowfall, and weather codes. It does not claim to predict non-weather incidents.<p style="margin:7px 0 0">${escapeHTML(forecast.risk_method)}</p></div>
    <div class="section-title"><h2>Monitored logistics hubs</h2><span>Forecast issued ${escapeHTML(dateText(forecast.retrieved_at))} · ${Number(forecast.forecast_window_hours)} hours</span></div>
    <div class="forecast-grid">${forecast.locations.map((location) => {
      const levelClass = String(location.risk_level).toLowerCase();
      const metrics = location.metrics || {};
      return `<article class="forecast-card">
        <div class="forecast-card-head"><div><div class="eyebrow">LOGISTICS HUB</div><h3>${escapeHTML(location.name)}</h3></div><div class="forecast-score">${Number(location.risk_score)}<small style="font:500 9px 'DM Sans',sans-serif;color:#909bac"> / 100</small></div></div>
        <div style="display:flex;align-items:center;justify-content:space-between">${severity(location.risk_level)}<span class="event-meta">${escapeHTML(location.forecast_start || "")} UTC start</span></div>
        <div class="forecast-meter"><span class="${escapeHTML(levelClass)}" style="width:${Math.max(3, Math.min(100, Number(location.risk_score)))}%"></span></div>
        <div class="forecast-metrics">
          ${forecastMetric("Max wind gust", `${Number(metrics.wind_gust_max_kmh).toFixed(1)} km/h`)}
          ${forecastMetric("Max wind", `${Number(metrics.wind_speed_max_kmh).toFixed(1)} km/h`)}
          ${forecastMetric("Hourly precipitation", `${Number(metrics.precipitation_max_mm).toFixed(1)} mm`)}
          ${forecastMetric("Hourly snowfall", `${Number(metrics.snowfall_max_cm).toFixed(1)} cm`)}
        </div><p class="forecast-reasons">${(location.reasons || []).map(escapeHTML).join(" · ")}</p>
      </article>`;
    }).join("")}</div>
    <div class="section-title"><h2>Data provenance</h2><span>Real-time source and saved snapshots</span></div>
    <section class="panel"><div class="status-card"><div><strong>${escapeHTML(forecast.data_source)}</strong><small>Hourly weather forecast · Retrieved ${escapeHTML(dateText(forecast.retrieved_at))}</small></div><a class="btn btn-small" href="${escapeHTML(safeURL(forecast.attribution_url))}" target="_blank" rel="noreferrer">Source & methodology ↗</a></div>
      <div class="status-card"><div><strong>Raw API payload</strong><small>Original public data, saved locally</small></div><code>${escapeHTML(forecast.raw_snapshot)}</code></div>
      <div class="status-card"><div><strong>Processed forecast</strong><small>JSON and CSV risk-index snapshots</small></div><code>${escapeHTML(forecast.processed_snapshot.replace(".json", ".json / .csv"))}</code></div>
    </section>`;
}
function forecastMetric(label, value) {
  return `<div class="forecast-metric"><small>${escapeHTML(label)}</small><strong>${escapeHTML(value)}</strong></div>`;
}
function statCard(label, value, note, icon) {
  return `<article class="stat-card"><div class="stat-top"><span>${label}</span><span class="stat-icon">${icon}</span></div><strong class="stat-value">${Number(value || 0).toLocaleString()}</strong><div class="stat-note">${note}</div></article>`;
}

async function renderDisruptions() {
  await loadCommon();
  $("#page-content").innerHTML = `
    ${pageHeading("Live network signals", "Disruptions, in focus.", "Monitor incoming logistics events, filter by what matters, and move from alert to operational brief.", `<button class="btn btn-primary" data-action="collect">↻ Run live collection</button>`)}
    <div class="filter-bar">
      <div class="field"><label for="disruption-search">Search events</label><input id="disruption-search" type="search" placeholder="Search title, location, description…"></div>
      <div class="field"><label for="disruption-category">Category</label><select id="disruption-category"><option value="">All categories</option>${categoryOptions()}</select></div>
      <div class="field"><label for="disruption-severity">Severity</label><select id="disruption-severity"><option value="">All priorities</option>${["Critical","High","Medium","Low","Unknown"].map((item) => `<option>${item}</option>`).join("")}</select></div>
      <div class="field"><label for="disruption-sort">Order</label><select id="disruption-sort"><option value="latest">Latest arrival</option><option value="priority">Highest severity</option></select></div>
    </div>
    <div class="section-title"><h2>Incident feed</h2><span id="disruption-count"></span></div>
    <div class="incident-grid" id="incident-list"></div>`;
  renderIncidentList();
}
function renderIncidentList() {
  const query = ($("#disruption-search")?.value || "").trim().toLowerCase();
  const category = $("#disruption-category")?.value || "";
  const level = $("#disruption-severity")?.value || "";
  const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
  const items = cachedDisruptions.filter((item) => {
    const text = [item.title, item.description, item.location].join(" ").toLowerCase();
    return (!query || text.includes(query)) && (!category || item.category === category) && (!level || String(item.severity).toLowerCase() === level.toLowerCase());
  });
  if ($("#disruption-sort")?.value === "priority") items.sort((a, b) => (priorityOrder[String(b.severity).toLowerCase()] || 0) - (priorityOrder[String(a.severity).toLowerCase()] || 0));
  $("#disruption-count").textContent = `${items.length} matching · ${cachedDisruptions.length} total`;
  $("#incident-list").innerHTML = items.length ? items.map((item) => {
    const source = safeURL(item.source_url);
    return `<article class="incident-card">
      <div class="incident-card-head">${severity(item.severity)}<span class="tag">${escapeHTML(item.category || "Other")}</span></div>
      <h3>${escapeHTML(item.title || "Untitled disruption")}</h3>
      <p>${escapeHTML(item.description || "No additional description available.")}</p>
      <div class="incident-details"><span>⌖ ${escapeHTML(item.location || "Unspecified")}</span><span>◷ ${escapeHTML(dateText(item.collected_at))}</span><span>${escapeHTML(item.source_name || "Unknown source")}${item.is_demo ? " · Demo" : ""}</span></div>
      <div class="incident-actions">${source ? `<a class="btn btn-small" href="${escapeHTML(source)}" target="_blank" rel="noreferrer">↗ Source</a>` : ""}
        <button class="btn btn-small" data-action="compare" data-id="${escapeHTML(item.id)}">⟷ Compare precedent</button>
        <button class="btn btn-primary btn-small" data-action="generate-report" data-id="${escapeHTML(item.id)}">✦ Generate brief</button></div>
    </article>`;
  }).join("") : `<div class="panel" style="grid-column:1/-1">${empty("No disruptions match the selected filters.")}</div>`;
}

async function renderCollection() {
  const [sources, logs, status, integrations] = await Promise.all([api("sources"), api("logs?limit=15"), api("health"), api("integrations")]);
  const sourceNotice = `<div class="notice">Collection uses the official NOAA active-alert feed without a key. Other configured website feeds require <code>FIRECRAWL_API_KEY</code>. When access is unavailable, the app reports an error instead of creating sample records.</div>`;
  $("#page-content").innerHTML = `
    ${pageHeading("Ingestion & source management", "Keep your signals flowing.", "Manage public monitoring feeds, run the processing pipeline, and inspect an auditable history of collection activity.")}
    ${sourceNotice}
    <div class="content-grid">
      <section class="form-panel"><h2>Run collection pipeline</h2><p>Fetch, clean, categorize, and persist the latest updates from your configured feeds.</p>
        <div class="callout">Pipeline status: <strong>${escapeHTML(status.status === "ok" ? "API online" : "API unavailable")}</strong><br>Website scraping key: <strong>${integrations.firecrawl_configured ? "configured" : "not configured"}</strong>. Each run records source-level results in the audit log.</div>
        <div class="form-actions"><button class="btn btn-primary" data-action="collect">⚡ Run full collection</button></div>
        <hr style="border:0;border-top:1px solid #edf0f4;margin:20px 0">
        <h2>Register a monitoring feed</h2><p>Add a publicly accessible source for future collection runs.</p>
        <form id="source-form"><div class="form-grid">
          <div class="field"><label for="source-name">Source name</label><input id="source-name" name="name" required minlength="2" placeholder="e.g. Port Authority Updates"></div>
          <div class="field"><label for="source-category">Expected category</label><select id="source-category" name="category">${categoryOptions("Port Disruption")}</select></div>
          <div class="field full"><label for="source-url">Website URL</label><input id="source-url" name="url" type="url" required placeholder="https://example.com/alerts"></div>
        </div><div class="form-actions"><button class="btn btn-primary" type="submit">＋ Add feed</button></div></form>
      </section>
      <section class="form-panel"><div class="panel-heading"><div><h2>Configured feeds</h2><p>${sources.length} monitored sources</p></div></div>
        <div class="source-list">${sources.length ? sources.map((source) => {
          const href = safeURL(source.url);
          return `<div class="source-item"><div><strong>${escapeHTML(source.name)}</strong><span class="tag">${escapeHTML(source.category)}</span>${href ? `<a href="${escapeHTML(href)}" target="_blank" rel="noreferrer">${escapeHTML(source.url)}</a>` : ""}</div><button class="btn btn-danger btn-small" data-action="delete-source" data-id="${escapeHTML(source.id)}">Remove</button></div>`;
        }).join("") : empty("No feeds are configured yet.")}</div>
      </section>
    </div>
    <div class="section-title"><h2>Collection audit log</h2><span>Most recent 15 runs</span></div>
    <div class="callout" style="margin:14px 0">Dataset locations: raw source payloads in <code>data/raw/</code>; normalized disruption snapshots in <code>data/processed/</code>; live events in SQLite at <code>database/app.db</code>.</div>
    <div class="table-wrap">${logs.length ? `<table><thead><tr><th>Run time</th><th>Source</th><th>Status</th><th>Records</th><th>Notes</th></tr></thead><tbody>${logs.map((log) => `<tr><td>${escapeHTML(dateText(log.created_at))}</td><td>${escapeHTML(log.source_url || "—")}</td><td><span class="${log.status === "success" ? "status-ok" : "status-warn"}">${escapeHTML(log.status || "—")}</span></td><td>${Number(log.records_count || 0)}</td><td>${escapeHTML(log.error_message || "—")}</td></tr>`).join("")}</tbody></table>` : empty("No collection runs have been recorded.")}</div>`;
}

async function renderHistory() {
  const [events, status] = await Promise.all([api("historical-events"), api("memento/status")]);
  $("#page-content").innerHTML = `
    ${pageHeading("Historical context & lessons", "Learn from what came before.", "Browse stored incidents, mitigation actions, and observed outcomes. Add a precedent to strengthen future comparisons.")}
    <div class="callout" style="margin-bottom:13px">Historical store: <strong>${escapeHTML(status.adapter || "SQLite Historical Event Store")}</strong> · ${status.is_live ? "Cloud connected" : "Local SQLite database"}</div>
    <div class="content-grid">
      <section><div class="filter-bar" style="grid-template-columns:1fr 1.2fr"><div class="field"><label for="history-category">Category</label><select id="history-category"><option value="">All categories</option>${categoryOptions()}</select></div><div class="field"><label for="history-search">Search precedent</label><input id="history-search" type="search" placeholder="Title, location, keyword…"></div></div>
        <div class="section-title" style="margin-top:5px"><h2>Precedent library</h2><span id="history-count">${events.length} records</span></div>
        <div id="history-list">${renderHistoryCards(events)}</div>
      </section>
      <section class="form-panel"><h2>Add historical precedent</h2><p>Record a verified event together with the response and outcome observed.</p>
        <form id="history-form"><div class="form-grid">
          <div class="field full"><label for="history-title">Incident title</label><input id="history-title" name="title" required minlength="3" placeholder="e.g. Port terminal outage"></div>
          <div class="field full"><label for="history-description">Description</label><textarea id="history-description" name="description" required minlength="5" placeholder="What happened?"></textarea></div>
          <div class="field"><label for="history-category-input">Category</label><select id="history-category-input" name="category">${categoryOptions("Port Disruption")}</select></div>
          <div class="field"><label for="history-severity">Severity</label><select id="history-severity" name="severity">${["Critical","High","Medium","Low"].map((x) => `<option>${x}</option>`).join("")}</select></div>
          <div class="field"><label for="history-location">Location</label><input id="history-location" name="location" placeholder="City, country"></div>
          <div class="field"><label for="history-url">Source URL</label><input id="history-url" name="source_url" type="url" required placeholder="https://…"></div>
          <div class="field full"><label for="history-response">Operational response</label><textarea id="history-response" name="response" required minlength="5" placeholder="Actions taken to mitigate the disruption"></textarea></div>
          <div class="field full"><label for="history-outcome">Observed outcome</label><textarea id="history-outcome" name="outcome" required minlength="5" placeholder="Measured result or resolution timeline"></textarea></div>
        </div><div class="form-actions"><button class="btn btn-primary" type="submit">Save precedent</button></div></form>
      </section>
    </div>`;
  window.historyEvents = events;
}
function renderHistoryCards(events) {
  if (!events.length) return empty("No historical events match this search.");
  return events.map((event) => `<article class="history-card"><details><summary><span>${severity(event.severity)} <strong style="display:inline;margin-left:6px">${escapeHTML(event.title)}</strong><small>${escapeHTML(event.category)} · ${escapeHTML(event.location || "Unspecified")}</small></span><span class="tag">${event.is_demo ? "Demo record" : "Stored precedent"}</span></summary>
    <div class="history-body"><p>${escapeHTML(event.description)}</p><div class="match-columns"><div><h4>Operational response</h4><p>${escapeHTML(event.response || "No response recorded.")}</p></div><div><h4>Observed outcome</h4><p>${escapeHTML(event.outcome || "No outcome recorded.")}</p></div></div>
    ${safeURL(event.source_url) ? `<a href="${escapeHTML(safeURL(event.source_url))}" target="_blank" rel="noreferrer">Open source ↗</a>` : ""}<p>Recorded ${escapeHTML(dateText(event.created_at || event.published_date))}</p></div></details></article>`).join("");
}
function filterHistory() {
  const category = $("#history-category")?.value || "";
  const query = ($("#history-search")?.value || "").toLowerCase();
  const events = (window.historyEvents || []).filter((event) =>
    (!category || event.category === category) &&
    (!query || [event.title, event.description, event.location].join(" ").toLowerCase().includes(query))
  );
  $("#history-count").textContent = `${events.length} records`;
  $("#history-list").innerHTML = renderHistoryCards(events);
}

async function renderComparison(selectedId = "") {
  await loadCommon();
  if (!cachedDisruptions.length) {
    $("#page-content").innerHTML = `${pageHeading("Precedent analysis", "Compare an active disruption.", "Use historical evidence to understand similarities, response patterns, and operational differences.")}<div class="panel">${empty("No disruptions are available. Run collection or add incoming events first.")}<div style="text-align:center"><a class="btn btn-primary" href="#/collection">Open collection</a></div></div>`;
    return;
  }
  $("#page-content").innerHTML = `
    ${pageHeading("Precedent analysis", "Compare an active disruption.", "Use historical evidence to understand similarities, response patterns, and operational differences.")}
    <div class="panel comparison-controls"><div class="field"><label for="compare-event">Select an active event</label><select id="compare-event">${eventOptions(selectedId)}</select></div><button class="btn btn-primary" data-action="run-comparison">⟷ Analyze precedent matches</button></div>
    <div id="comparison-results"></div>`;
  if (selectedId) runComparison(selectedId);
}
async function runComparison(eventId = $("#compare-event")?.value) {
  const event = cachedDisruptions.find((item) => item.id === eventId);
  const results = $("#comparison-results");
  if (!event || !results) return;
  results.innerHTML = `<div class="loading-state"><span class="spinner"></span>Comparing against historical memory…</div>`;
  try {
    const data = await post(`compare/${encodeURIComponent(eventId)}`);
    const matches = data.similar_events || [];
    results.innerHTML = `<section class="panel comparison-event"><div class="eyebrow">CURRENT DISRUPTION</div><h3>${escapeHTML(event.title)}</h3><p>${escapeHTML(event.description)}</p><div class="event-details">${severity(event.severity)} <span class="tag">${escapeHTML(event.category)}</span><span class="tag">${escapeHTML(event.location || "Unspecified")}</span></div></section>
      <div class="section-title"><h2>Historical matches</h2><span>${matches.length} relevant precedents found</span></div>
      ${matches.length ? matches.map((match, index) => {
        const score = Math.max(0, Math.min(100, Number(match.similarity_percentage || 0)));
        return `<article class="panel match-card"><div class="match-top"><div><div class="eyebrow">MATCH ${String(index + 1).padStart(2, "0")} · ${escapeHTML(match.category || "Historical event")}</div><h3 style="margin:0 0 5px;font-size:13px">${escapeHTML(match.title || match.event?.title || "Historical precedent")}</h3><span class="tag">${escapeHTML(match.location || match.event?.location || "Unspecified")}</span></div><div class="match-score">${score.toFixed(1)}%</div></div>
        <div class="match-progress"><span style="width:${score}%"></span></div><div class="match-columns"><div><h4>Response & outcome</h4><p><strong>Response:</strong> ${escapeHTML(match.previous_response || "Not recorded.")}</p><p><strong>Outcome:</strong> ${escapeHTML(match.historical_outcome || "Not recorded.")}</p></div>
        <div><h4>Operational observations</h4>${listItems(match.operational_observations)}<h4 style="margin-top:10px">Key differences</h4>${listItems(match.key_differences)}</div></div></article>`;
      }).join("") : `<div class="panel">${empty("No historical incidents met the similarity threshold.")}</div>`}`;
  } catch (error) {
    results.innerHTML = `<div class="panel">${empty(error.message)}</div>`;
  }
}
function listItems(items) {
  return Array.isArray(items) && items.length ? `<ul>${items.map((item) => `<li>${escapeHTML(item)}</li>`).join("")}</ul>` : `<p>No additional observations.</p>`;
}

async function renderReports() {
  await loadCommon();
  const reports = await api("reports");
  $("#page-content").innerHTML = `
    ${pageHeading("Decision support", "Operational reports.", "Generate 13-section summaries from recorded disruption evidence and historical memory. Download PDF or plain text for your team.")}
    <div class="content-grid">
      <section class="form-panel"><h2>Create a new report</h2><p>Select an active incident to create a summary from its recorded facts and stored precedents.</p>
        <div class="callout">Reports are generated locally from recorded application data. No external AI provider or API key is needed; this is a template-based summary, not generative AI.</div>
        ${cachedDisruptions.length ? `<div class="field"><label for="report-event">Disruption</label><select id="report-event">${eventOptions()}</select></div><div class="form-actions"><button class="btn btn-primary" data-action="generate-report" data-from-select="true">✦ Generate 13-section report</button></div>` : empty("No disruptions are available to report on.")}
        <div id="active-report"></div>
      </section>
      <section><div class="panel-heading"><div><h2 style="margin:0;font-size:14px">Report archive</h2><p style="margin:5px 0;color:#929eae;font-size:9px">${reports.length} reports saved</p></div></div>
        <div class="source-list">${reports.length ? reports.map((report) => `<div class="source-item"><div><strong>Report · ${escapeHTML(report.disruption_id || report.id)}</strong><span class="tag">${escapeHTML(report.llm_provider || "Local evidence-based template (not AI)")}</span><a>${escapeHTML(dateText(report.generated_at))}</a></div><button class="btn btn-small" data-action="open-report" data-id="${escapeHTML(report.id)}">View report</button></div>`).join("") : empty("Generated reports will be available here.")}</div>
      </section>
    </div>`;
  if (latestReport) displayReport(latestReport);
}
function displayReport(report) {
  latestReport = report;
  const target = $("#active-report");
  if (!target) return;
  target.innerHTML = `<div class="section-title"><h2>Report · ${escapeHTML(report.disruption_id || report.id)}</h2><span>${escapeHTML(dateText(report.generated_at))}</span></div>
    <div class="report-meta"><span class="tag">Generator · ${escapeHTML(report.llm_provider || "Local evidence-based template (not AI)")}</span><span class="tag">13-section format</span></div>
    <pre class="report-content">${escapeHTML(report.content || "No report content.")}</pre>
    <div class="heading-actions" style="margin-top:10px"><a class="btn btn-primary" href="/api/reports/${encodeURIComponent(report.id)}/pdf" download>↓ Download PDF</a><button class="btn" data-action="download-text" data-id="${escapeHTML(report.id)}">↓ Download text</button></div>`;
}

async function renderSettings() {
  const [health, memento, stats, integrations] = await Promise.all([api("health"), api("memento/status"), api("stats"), api("integrations")]);
  const online = health.status === "ok";
  $("#page-content").innerHTML = `
    ${pageHeading("Platform health", "A clear view of system status.", "Check core service health, historical memory connectivity, and API entry points. Credentials are never exposed in this screen.")}
    <div class="content-grid">
      <section class="panel"><div class="panel-heading"><div><h3>Service diagnostics</h3><p>Current runtime integration status</p></div><button class="btn btn-small" data-action="refresh">↻ Refresh status</button></div>
        ${statusRow("FastAPI core", online ? "Online and responding" : "Unavailable", online, "REST routes and dashboard are served by this process.")}
        ${statusRow("Historical memory", memento.is_live ? "Cloud connected" : "Local SQLite store", true, memento.adapter || "Historical events use local storage.")}
        ${statusRow("24-hour weather forecast", "Live public data", true, integrations.forecast_source)}
        ${statusRow("Report generation", "Available locally", true, "Evidence-based template; no external AI provider or API key is used.")}
        ${statusRow("Website collection", integrations.firecrawl_configured ? "Firecrawl configured" : "NOAA alerts only", true, integrations.firecrawl_configured ? "Configured public web feeds are enabled." : "Set FIRECRAWL_API_KEY to scrape configured websites.")}
        ${statusRow("Database", "Connected", true, `${Number(stats.total_disruptions || 0)} disruption records · ${Number(stats.sources_count || 0)} monitoring sources`)}
        ${statusRow("Interactive API docs", "Available", true, "Explore request schemas and endpoints at /docs.")}
        <div class="heading-actions" style="margin-top:14px"><a class="btn btn-primary" href="/docs" target="_blank" rel="noreferrer">Open API documentation ↗</a><a class="btn" href="/api/health" target="_blank" rel="noreferrer">Health endpoint ↗</a></div>
      </section>
      <section class="panel"><div class="panel-heading"><div><h3>Platform modules</h3><p>Capabilities of the operations workspace</p></div></div>
        <div class="team-grid">
          ${teamItem("01 · Data collection", "Public source management, ingestion runs, and collection audit logs.")}
          ${teamItem("02 · Data processing", "Normalization, categorization, duplicate detection, and evidence-based severity.")}
          ${teamItem("03 · Historical memory", "Precedent storage, response tracking, and similarity comparison.")}
          ${teamItem("04 · Intelligence briefs", "Grounded 13-section reports with PDF export.")}
        </div>
        <div class="callout" style="margin-top:12px">From the project folder, run <code>./run.sh</code>. The server starts and opens the dashboard automatically.</div>
      </section>
    </div>`;
}
function statusRow(title, status, ok, description) {
  return `<div class="status-card"><div><strong>${escapeHTML(title)}</strong><small>${escapeHTML(description)}</small></div><span class="${ok ? "status-ok" : "status-bad"}">● ${escapeHTML(status)}</span></div>`;
}
function teamItem(title, description) {
  return `<div class="team-item"><strong>${escapeHTML(title)}</strong><p>${escapeHTML(description)}</p></div>`;
}

async function navigate() {
  const [page, routeId] = (window.location.hash.replace(/^#\/?/, "") || "overview").split("/");
  const selectedEventId = routeId ? decodeURIComponent(routeId) : "";
  currentPage = PAGE_TITLES[page] ? page : "overview";
  if (!window.location.hash || !PAGE_TITLES[page]) window.history.replaceState(null, "", "#/overview");
  document.querySelectorAll("[data-page]").forEach((link) => link.classList.toggle("active", link.dataset.page === currentPage));
  $("#breadcrumb-current").textContent = PAGE_TITLES[currentPage];
  $("#sidebar").classList.remove("open");
  $("#page-content").innerHTML = `<div class="loading-state"><span class="spinner"></span>Loading ${escapeHTML(PAGE_TITLES[currentPage].toLowerCase())}…</div>`;
  try {
    const renderers = {
      overview: renderOverview, forecast: renderForecast, disruptions: renderDisruptions, collection: renderCollection,
      history: renderHistory, comparison: () => renderComparison(selectedEventId), reports: renderReports, settings: renderSettings,
    };
    await renderers[currentPage]();
  } catch (error) {
    $("#page-content").innerHTML = `${pageHeading("Service unavailable", "Unable to load this view.", "The FastAPI service returned an error while loading this page.")}<div class="panel"><p style="color:#bb4b53;font-size:11px">${escapeHTML(error.message)}</p><button class="btn btn-primary" data-action="refresh">Try again</button></div>`;
    toast(error.message, "error");
  }
}
async function refreshHealth() {
  const dot = $("#health-dot");
  try {
    const data = await api("health");
    dot.className = data.status === "ok" ? "online" : "offline";
    $("#health-label").textContent = data.status === "ok" ? "API connected" : "API unavailable";
  } catch {
    dot.className = "offline";
    $("#health-label").textContent = "API unavailable";
  }
}
async function runCollection(button) {
  setBusy(button, true, "Collecting…");
  try {
    const result = await post("collect");
    const message = result.status === "success"
      ? `Collection complete · ${result.stored || 0} stored from ${result.sources_scraped || 0} sources`
      : (result.message || "Collection finished without new records.");
    toast(message, result.status === "success" ? "success" : "error");
    await navigate();
  } catch (error) { toast(error.message, "error"); }
  finally { setBusy(button, false); }
}
async function generateReport(eventId, button) {
  if (!eventId) return;
  setBusy(button, true, "Generating…");
  try {
    const report = await post("reports/generate", { event_id: eventId });
    latestReport = report;
    if (currentPage !== "reports") window.location.hash = "#/reports";
    else displayReport(report);
    toast("Operational brief generated successfully.");
  } catch (error) { toast(error.message, "error"); }
  finally { setBusy(button, false); }
}
function downloadText(report) {
  const blob = new Blob([report.content || ""], { type: "text/plain;charset=utf-8" });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = `logistics_brief_${report.id}.txt`;
  link.click();
  URL.revokeObjectURL(href);
}

document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const action = button.dataset.action;
  try {
    if (action === "collect") await runCollection(button);
    if (action === "refresh") await navigate();
    if (action === "compare") {
      window.location.hash = `#/comparison/${encodeURIComponent(button.dataset.id)}`;
    }
    if (action === "run-comparison") await runComparison();
    if (action === "generate-report") {
      const eventId = button.dataset.fromSelect ? $("#report-event")?.value : button.dataset.id;
      await generateReport(eventId, button);
    }
    if (action === "delete-source") {
      if (!window.confirm("Remove this monitoring source?")) return;
      await remove(`sources/${encodeURIComponent(button.dataset.id)}`);
      toast("Monitoring source removed.");
      await renderCollection();
    }
    if (action === "open-report") {
      const report = await api(`reports/${encodeURIComponent(button.dataset.id)}`);
      displayReport(report);
    }
    if (action === "download-text" && latestReport) downloadText(latestReport);
  } catch (error) { toast(error.message, "error"); }
});
document.addEventListener("input", (event) => {
  if (["disruption-search"].includes(event.target.id)) renderIncidentList();
  if (event.target.id === "history-search") filterHistory();
});
document.addEventListener("change", (event) => {
  if (["disruption-category", "disruption-severity", "disruption-sort"].includes(event.target.id)) renderIncidentList();
  if (["history-category"].includes(event.target.id)) filterHistory();
});
document.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form).entries());
  const button = form.querySelector('button[type="submit"]');
  setBusy(button, true, "Saving…");
  try {
    if (form.id === "source-form") {
      await post("sources", data);
      toast("Monitoring feed registered.");
      await renderCollection();
    } else if (form.id === "history-form") {
      data.source_name = "Manual Operations Input";
      data.location ||= "Unspecified";
      await post("historical-events", data);
      toast("Historical precedent saved.");
      await renderHistory();
    }
  } catch (error) { toast(error.message, "error"); }
  finally { setBusy(button, false); }
});
$("#mobile-menu").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
window.addEventListener("hashchange", navigate);
navigate();
refreshHealth();
setInterval(refreshHealth, 30000);
