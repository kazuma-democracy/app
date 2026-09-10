import { searchCompanies } from "./search.mjs";

const api = globalThis.browser ?? globalThis.chrome;
const PACK_PATH = "data/wa-public-evidence-pack.json";
const DEFAULT_PROFILE = "public:information-only:v1";
const PROFILES = [
  ["public:information-only:v1", "profileInfo"],
  ["public:strict-military-specific:v1", "profileMilitary"],
];
const PROFILE_IDS = new Set(PROFILES.map(([value]) => value));
const VISIBLE_TOPICS = new Set(["military_defence"]);
const VISIBLE_EVIDENCE_CATEGORIES = new Set(["military_contract"]);

const form = document.querySelector("#search-form");
const query = document.querySelector("#query");
const profile = document.querySelector("#profile");
const status = document.querySelector("#status");
const results = document.querySelector("#results");
const detail = document.querySelector("#detail");
const pageHintButton = document.querySelector("#page-hint");
let pack = null;
let selectedCompany = null;

function t(key) {
  return api?.i18n?.getMessage(key) || key;
}

function element(tag, text, className = "") {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = String(text);
  if (className) node.className = className;
  return node;
}

function stateText(state) {
  return t(`state${String(state || "UNKNOWN").toUpperCase()}`);
}

function localize() {
  for (const node of document.querySelectorAll("[data-i18n]")) {
    node.textContent = t(node.dataset.i18n);
  }
  query.placeholder = t("searchPlaceholder");
  for (const [value, key] of PROFILES) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = t(key);
    profile.append(option);
  }
}

function appendField(parent, labelKey, value) {
  const line = element("p");
  const label = element("strong", `${t(labelKey)}: `);
  line.append(label, document.createTextNode(String(value ?? "")));
  parent.append(line);
}

function renderTopics(parent, company) {
  const labels = {
    military_defence: "militaryTopic",
  };

  for (const [topicId, topic] of Object.entries(company.topics ?? {})) {
    if (!VISIBLE_TOPICS.has(topicId)) continue;
    const card = element("section", undefined, "card");
    card.append(element("h3", t(labels[topicId] ?? topicId)));
    card.append(element("p", stateText(topic.state)));
    if (topic.reason) card.append(element("p", topic.reason, "meta"));
    parent.append(card);
  }
}

function safeLink(url, text) {
  if (typeof url !== "string" || !url.startsWith("https://")) {
    return element("span", text);
  }
  const link = element("a", text);
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function renderEvidence(parent, company) {
  const section = element("section", undefined, "card");
  section.append(element("h3", t("evidenceLabel")));
  const visibleEvidence = (company.evidence ?? []).filter((evidence) =>
    VISIBLE_EVIDENCE_CATEGORIES.has(evidence?.narrow_claim?.category),
  );
  if (!visibleEvidence.length) {
    section.append(element("p", stateText("NO_MATCH")));
  }
  for (const evidence of visibleEvidence) {
    const item = element("article");

    const claim = evidence.narrow_claim ?? {};
    item.append(element("p", `${claim.category ?? ""} / ${claim.predicate ?? ""}`));
    if (claim.value !== undefined) {
      item.append(element("pre", JSON.stringify(claim.value, null, 2)));
    }
    for (const source of evidence.sources ?? []) {
      const sourceLine = element("p");
      sourceLine.append(
        element("strong", `${t("sourceLabel")}: `),
        safeLink(source.url, source.publisher || source.source_id || source.url),
      );
      item.append(sourceLine);
      appendField(item, "evidenceDateLabel", source.evidence_date);
      appendField(item, "retrievedAtLabel", source.retrieved_at);
      if (source.locator) item.append(element("p", source.locator, "meta"));
    }
    if (evidence.challenge_url) {
      item.append(safeLink(evidence.challenge_url, t("challengeLabel")));
    }
    section.append(item);
  }
  parent.append(section);
}

function renderCompany(company) {
  selectedCompany = company;
  detail.replaceChildren();
  detail.hidden = false;
  detail.append(element("h2", company.canonical_name));

  appendField(detail, "securityCodeLabel", company.security_code);
  appendField(detail, "identityLabel", company.identity_state);

  const view = (company.policy_views ?? []).find(
    (item) => item.profile_id === profile.value,
  );
  appendField(detail, "policyResultLabel", view?.decision ?? "NONE");
  detail.append(element("p", t("noneWarning"), "warning"));
  if (view?.reasoning) detail.append(element("p", view.reasoning, "meta"));

  renderTopics(detail, company);
  renderEvidence(detail, company);
  appendField(detail, "packVersionLabel", pack?.manifest?.pack_version);
  appendField(detail, "generatedAtLabel", pack?.manifest?.generated_at);
}

function renderCandidates(candidates) {
  results.replaceChildren();
  detail.hidden = true;
  if (!candidates.length) {
    status.textContent = t("noResults");
    return;
  }
  status.textContent = t("chooseCompany");
  for (const company of candidates) {
    const button = element(
      "button",
      `${company.canonical_name} (${company.security_code || "-"})`,
      "candidate",
    );

    button.type = "button";
    button.addEventListener("click", () => renderCompany(company));
    results.append(button);
  }
}

async function loadPack() {
  const response = await fetch(api.runtime.getURL(PACK_PATH));
  if (!response.ok) throw new Error(`pack load failed: ${response.status}`);
  return response.json();
}

async function initialize() {
  localize();
  const stored = await api.storage.local.get("profile_id");
  const storedProfile = stored?.profile_id;
  profile.value = PROFILE_IDS.has(storedProfile) ? storedProfile : DEFAULT_PROFILE;
  pack = await loadPack();
  status.textContent = "";
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  renderCandidates(searchCompanies(pack, query.value));
});

profile.addEventListener("change", async () => {
  await api.storage.local.set({ profile_id: profile.value });
  if (selectedCompany) renderCompany(selectedCompany);
});

pageHintButton.addEventListener("click", async () => {
  try {
    const [tab] = await api.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) throw new Error("active tab unavailable");
    const injected = await api.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["page-hint.js"],
    });
    const pageHint = injected?.[0]?.result ?? {};
    const hintQuery = pageHint.selectedText || pageHint.title || "";
    query.value = hintQuery;
    renderCandidates(searchCompanies(pack, hintQuery));
  } catch {
    status.textContent = t("pageHintUnavailable");
  }
});

initialize().catch(() => {
  status.textContent = t("loadError");
});
