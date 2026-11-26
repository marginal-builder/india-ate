import {
  getFactReceiptFromSeed,
  getVerifiedNearbyFromSeed,
} from "../data/seed";
import {
  DEFAULT_API_BASE,
  checkApiHealth,
  fetchFactReceipt,
  fetchVerifiedNearby,
  submitGrievancePacket,
} from "../lib/api";
import { withBase } from "../lib/base";
import {
  decodeFssai14Offline,
  describeLicenseTierFact,
} from "../lib/fssai";
import { buildOfflineGrievancePacket } from "../lib/grievance";
import {
  receiptUsesSyntheticData,
  verificationTierLabel,
} from "../lib/provenance";
import type {
  FactReceipt,
  GrievanceCategory,
  GrievancePacket,
  VerifiedSwitchOption,
} from "../lib/types";

function el<T extends HTMLElement>(id: string): T {
  const node = document.getElementById(id);
  if (!node) {
    throw new Error(`Missing element #${id}`);
  }
  return node as T;
}

function escapeHtml(text: string): string {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function safeHttpUrl(rawUrl: string): string {
  try {
    const parsed = new URL(rawUrl);
    if (parsed.protocol === "https:" || parsed.protocol === "http:") {
      return parsed.toString();
    }
  } catch {
    // fall through
  }
  return "#";
}

export function renderReceiptHtml(
  receipt: FactReceipt,
  sourceLabel: string,
): string {
  const tierFact = describeLicenseTierFact(receipt.decoded);
  const synthetic = receiptUsesSyntheticData(receipt);
  const verifiedBadge = synthetic
    ? "Synthetic demo — not an official record"
    : receipt.last_verified_at
      ? `Last provenance snapshot: ${escapeHtml(receipt.last_verified_at)}`
      : "Offline ID Decode Only (Not Cached in Registry)";

  const premisesHtml = receipt.premises
    ? `
      <div style="margin-top:1rem;padding-top:0.85rem;border-top:1px solid var(--surface-alt);">
        <h3 style="margin:0 0 0.5rem;font-size:1rem;">${synthetic ? "Illustrative Physical Premises" : "Registered Physical Premises"}</h3>
        <dl class="kv-list">
          <div class="kv-item"><dt>${synthetic ? "Illustrative Name" : "Legal Name"}</dt><dd>${escapeHtml(receipt.premises.legal_name)}</dd></div>
          <div class="kv-item"><dt>Premises Type</dt><dd class="mono">${escapeHtml(receipt.premises.premises_type)}</dd></div>
          <div class="kv-item"><dt>Address</dt><dd>${escapeHtml(receipt.premises.address ?? "Not recorded")}</dd></div>
          <div class="kv-item"><dt>Pin Code</dt><dd class="mono">${receipt.premises.postal_code ? `<a href="${escapeHtml(withBase(`/in/pincode/${receipt.premises.postal_code}`))}">${escapeHtml(receipt.premises.postal_code)}</a>` : "Not recorded"}</dd></div>
        </dl>
      </div>
    `
    : "";

  const listingsHtml =
    receipt.brand_listings.length === 0
      ? `<p style="color:var(--text-muted);margin:0;">No platform storefront listings recorded for this 14-digit FSSAI ID.</p>`
      : `<div class="table-scroll"><table>
          <thead><tr><th>Display Name</th><th>Platform</th><th>Pin Code</th><th>First / Last Seen</th><th>Primary Source</th></tr></thead>
          <tbody>
            ${receipt.brand_listings
              .map(
                (l) => `<tr>
                  <td>${escapeHtml(l.display_name)}</td>
                  <td class="mono">${escapeHtml(l.platform)}</td>
                  <td class="mono">${escapeHtml(l.postal_code ?? "—")}</td>
                  <td class="mono">${escapeHtml(l.first_seen_at.slice(0, 10))} → ${escapeHtml(l.last_seen_at.slice(0, 10))}</td>
                  <td><a href="${escapeHtml(safeHttpUrl(l.provenance.source_url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(l.provenance.source_name)}</a></td>
                </tr>`,
              )
              .join("")}
          </tbody>
        </table></div>`;

  const eventsHtml =
    receipt.events.length === 0
      ? `<p style="color:var(--text-muted);margin:0;">${synthetic ? "No illustrative enforcement, recall, or hygiene events in this demo snapshot." : "No official enforcement, recall, or hygiene audit events recorded."}</p>`
      : `<div class="table-scroll"><table>
          <thead><tr><th>Date</th><th>Event Type</th><th>Verbatim Status</th><th>${synthetic ? "Illustrative Summary" : "Official Summary"}</th><th>Primary Source</th></tr></thead>
          <tbody>
            ${receipt.events
              .map(
                (ev) => `<tr>
                  <td class="mono">${escapeHtml(ev.event_date)}</td>
                  <td class="mono">${escapeHtml(ev.event_type)}</td>
                  <td><span class="badge">${escapeHtml(ev.status)}</span></td>
                  <td>
                    ${escapeHtml(ev.verbatim_summary)}
                    ${ev.batch_or_lot_no ? `<div class="mono" style="font-size:0.8rem;margin-top:0.2rem;">Batch/Lot: ${escapeHtml(ev.batch_or_lot_no)}</div>` : ""}
                  </td>
                  <td>
                    <a href="${escapeHtml(safeHttpUrl(ev.provenance.source_url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(ev.provenance.source_name)}</a>
                    <div><span class="badge">${escapeHtml(verificationTierLabel(ev.provenance.verification_tier))}</span></div>
                    <div class="mono" style="font-size:0.72rem;color:var(--text-muted);">sha256: ${escapeHtml(ev.provenance.content_sha256.slice(0, 12))}…</div>
                  </td>
                </tr>`,
              )
              .join("")}
          </tbody>
        </table></div>`;

  const centralRoHtml = receipt.decoded.central_regional_office
    ? `<div class="kv-item"><dt>Central Regional Office</dt><dd>${escapeHtml(receipt.decoded.central_regional_office)} (${escapeHtml(receipt.decoded.officer_jurisdiction_state ?? "")})</dd></div>`
    : "";

  return `
    <div class="card-header">
      <div>
        <h3 style="margin:0;font-size:1.15rem;">${synthetic ? "Illustrative" : ""} Fact Receipt: <span class="mono">${escapeHtml(receipt.fssai_id)}</span></h3>
        <span class="badge" style="margin-top:0.35rem;">${escapeHtml(sourceLabel)}</span>
      </div>
      <span class="badge">${verifiedBadge}</span>
    </div>
    ${
      synthetic
        ? `<div class="notice"><strong>Illustrative data only.</strong> This receipt comes from the repository's synthetic demo fixtures. The FSSAI ID is a format-valid example, not a statement about the real licensee.</div>`
        : ""
    }
    <div class="notice"><strong>License Tier (Statutory Rule):</strong> ${escapeHtml(tierFact)}</div>
    <dl class="kv-list">
      <div class="kv-item"><dt>Authority Scope</dt><dd>${receipt.decoded.authority_scope === "central" ? "Central Authority" : "State / UT Authority"}</dd></div>
      <div class="kv-item"><dt>State / UT</dt><dd>${escapeHtml(receipt.decoded.state_name)} (${escapeHtml(receipt.decoded.state_code)})</dd></div>
      <div class="kv-item"><dt>Registration Year</dt><dd class="mono">${receipt.decoded.registration_year}</dd></div>
      <div class="kv-item"><dt>Officer / Serial</dt><dd class="mono">${escapeHtml(receipt.decoded.officer_code)} / ${escapeHtml(receipt.decoded.serial)}</dd></div>
      ${centralRoHtml}
      <div class="kv-item"><dt>Ghost-Brand Cluster Count</dt><dd class="mono">${receipt.ghost_brand_count}</dd></div>
    </dl>
    ${premisesHtml}
    <div style="margin-top:1.1rem;">
      <h4 style="margin:0 0 0.5rem;">${synthetic ? "Illustrative Ghost-Brand Cluster" : "Ghost-Brand Cluster"} (${receipt.ghost_brand_count})</h4>
      ${listingsHtml}
    </div>
    <div style="margin-top:1.1rem;">
      <h4 style="margin:0 0 0.5rem;">${synthetic ? "Illustrative Records (Synthetic Demo)" : "Official Authoritative Records"} (${receipt.events.length})</h4>
      ${eventsHtml}
    </div>
  `;
}

export function renderNearbyHtml(
  postalCode: string,
  options: VerifiedSwitchOption[],
  sourceLabel: string,
): string {
  const synthetic =
    sourceLabel.toLowerCase().includes("synthetic") ||
    options.some((option) =>
      option.premises.provenance.some(
        (provenance) => provenance.verification_tier === "synthetic_demo",
      ),
    );
  if (options.length === 0) {
    return `<p style="margin:0;color:var(--text-muted);">No ${synthetic ? "illustrative" : "verified"} nearby switch options found for pin code <span class="mono">${escapeHtml(postalCode)}</span> (${escapeHtml(sourceLabel)}).</p>`;
  }
  return `
    <p style="margin:0 0 0.5rem;"><span class="badge">${escapeHtml(sourceLabel)}</span></p>
    <div class="table-scroll">
      <table>
        <thead><tr><th>${synthetic ? "Illustrative Name" : "Legal Name"}</th><th>Premises Type</th><th>${synthetic ? "Illustrative Basis" : "Verification Basis"}</th><th>Fact Receipt</th></tr></thead>
        <tbody>
          ${options
            .map((opt) => {
              const reg = opt.premises.regulatory_ids.find(
                (r) => r.scheme === "IN_FSSAI_14",
              );
              const link = reg
                ? `<a class="mono" href="${escapeHtml(withBase(`/in/license/${reg.raw_value}`))}">${escapeHtml(reg.raw_value)}</a>`
                : "—";
              return `<tr>
                <td>${escapeHtml(opt.premises.legal_name)}</td>
                <td class="mono">${escapeHtml(opt.premises.premises_type)}</td>
                <td>${escapeHtml(opt.verification_reasons.join(" · "))}</td>
                <td>${link}</td>
              </tr>`;
            })
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

export function renderGrievanceHtml(
  packet: GrievancePacket,
  sourceLabel: string,
): string {
  const summaryText = [
    `Food Safety Connect Grievance Packet (${packet.packet_id})`,
    `FSSAI ID: ${packet.fssai_id}`,
    `Premises Name: ${packet.premises_legal_name ?? "Not recorded"}`,
    `Jurisdiction: ${packet.decoded_jurisdiction.state_name} (${packet.decoded_jurisdiction.authority_scope})`,
    `Category: ${packet.issue_category}`,
    `Order Reference: ${packet.order_reference ?? "N/A"}`,
    `Incident Date: ${packet.incident_date}`,
    `15-Day State Escalation Deadline: ${packet.escalation_deadline}`,
    `Description: ${packet.description}`,
    `Portal: ${packet.portal_url}`,
  ].join("\n");

  return `
    <div class="card-header">
      <div>
        <h3 style="margin:0;font-size:1.05rem;">Grievance Packet Ready</h3>
        <span class="badge mono">Packet ID: ${escapeHtml(packet.packet_id)}</span>
        <span class="badge">${escapeHtml(sourceLabel)}</span>
      </div>
      <span class="badge mono">15-Day Escalation Deadline: ${escapeHtml(packet.escalation_deadline)}</span>
    </div>
    <dl class="kv-list">
      <div class="kv-item"><dt>FSSAI ID</dt><dd class="mono">${escapeHtml(packet.fssai_id)}</dd></div>
      <div class="kv-item"><dt>Jurisdiction</dt><dd>${escapeHtml(packet.decoded_jurisdiction.state_name)} (${escapeHtml(packet.decoded_jurisdiction.officer_code)})</dd></div>
      <div class="kv-item"><dt>Premises Name</dt><dd>${escapeHtml(packet.premises_legal_name ?? "Not recorded")}</dd></div>
      <div class="kv-item"><dt>Known Sourced Events</dt><dd class="mono">${packet.known_events_count}</dd></div>
    </dl>
    <div style="margin-top:0.85rem;">
      <label for="grievance-copy-box" style="display:block;font-size:0.8rem;font-weight:600;color:var(--text-muted);margin-bottom:0.25rem;">Structured Filing Text</label>
      <textarea id="grievance-copy-box" rows="7" readonly style="width:100%;font-family:var(--mono);font-size:0.82rem;">${escapeHtml(summaryText)}</textarea>
    </div>
    <div style="margin-top:0.75rem;display:flex;flex-wrap:wrap;gap:0.65rem;">
      <button type="button" id="copy-grievance-btn" class="secondary">Copy Packet Text</button>
      <a class="btn" href="${escapeHtml(safeHttpUrl(packet.portal_url))}" target="_blank" rel="noopener noreferrer">Open Food Safety Connect Portal →</a>
    </div>
  `;
}

export function initConsumerUi(): void {
  const apiBaseInput = el<HTMLInputElement>("api-base-url");
  const apiStatusBadge = el<HTMLSpanElement>("api-status-badge");
  const fssaiInput = el<HTMLInputElement>("fssai-input");
  const lookupForm = el<HTMLFormElement>("lookup-form");
  const lookupError = el<HTMLParagraphElement>("lookup-error");
  const receiptOutput = el<HTMLDivElement>("receipt-output");

  const nearbyForm = el<HTMLFormElement>("nearby-form");
  const pinInput = el<HTMLInputElement>("pin-input");
  const nearbyOutput = el<HTMLDivElement>("nearby-output");

  const grievanceForm = el<HTMLFormElement>("grievance-form");
  const gFssaiInput = el<HTMLInputElement>("g-fssai");
  const gCategorySelect = el<HTMLSelectElement>("g-category");
  const gDateInput = el<HTMLInputElement>("g-date");
  const gOrderInput = el<HTMLInputElement>("g-order");
  const gDescInput = el<HTMLTextAreaElement>("g-desc");
  const gPersistCheckbox = el<HTMLInputElement>("g-persist");
  const grievanceError = el<HTMLParagraphElement>("grievance-error");
  const grievanceOutput = el<HTMLDivElement>("grievance-output");

  let lastReceipt: FactReceipt | null = null;

  const getApiBase = (): string =>
    apiBaseInput.value.trim().replace(/\/+$/, "") || DEFAULT_API_BASE;

  async function refreshHealth(): Promise<boolean> {
    const ok = await checkApiHealth(getApiBase());
    apiStatusBadge.textContent = ok
      ? "Local API: connected"
      : "Local API: offline — synthetic demo fixtures";
    return ok;
  }

  async function runLookup(rawId: string): Promise<void> {
    lookupError.classList.add("hidden");
    try {
      decodeFssai14Offline(rawId);
    } catch (err) {
      lookupError.textContent =
        err instanceof Error ? err.message : "Invalid FSSAI ID";
      lookupError.classList.remove("hidden");
      return;
    }

    const cleanId = rawId.trim();
    gFssaiInput.value = cleanId;

    let receipt: FactReceipt;
    let sourceLabel: string;
    try {
      receipt = await fetchFactReceipt(cleanId, getApiBase());
      sourceLabel = "Source: live API (india-ate serve)";
    } catch {
      receipt = getFactReceiptFromSeed(cleanId);
      sourceLabel = "Source: offline decoder + synthetic demo fixtures";
    }

    lastReceipt = receipt;
    receiptOutput.innerHTML = renderReceiptHtml(receipt, sourceLabel);
    receiptOutput.classList.remove("hidden");

    if (receipt.premises?.postal_code) {
      pinInput.value = receipt.premises.postal_code;
      await runNearby(receipt.premises.postal_code);
    } else {
      nearbyOutput.innerHTML = "";
      nearbyOutput.classList.add("hidden");
    }
  }

  async function runNearby(rawPin: string): Promise<void> {
    const cleanPin = rawPin.trim();
    if (!cleanPin) return;
    let options: VerifiedSwitchOption[];
    let sourceLabel: string;
    try {
      const res = await fetchVerifiedNearby(cleanPin, getApiBase());
      options = res.options;
      sourceLabel = "Source: live API (india-ate serve)";
    } catch {
      options = getVerifiedNearbyFromSeed(cleanPin);
      sourceLabel = "Source: synthetic demo fixtures";
    }
    nearbyOutput.innerHTML = renderNearbyHtml(cleanPin, options, sourceLabel);
    nearbyOutput.classList.remove("hidden");
  }

  lookupForm.addEventListener("submit", (e) => {
    e.preventDefault();
    void runLookup(fssaiInput.value);
  });

  document.querySelectorAll<HTMLButtonElement>("[data-sample-fssai]").forEach(
    (btn) => {
      btn.addEventListener("click", () => {
        const val = btn.dataset.sampleFssai ?? "";
        fssaiInput.value = val;
        void runLookup(val);
      });
    },
  );

  nearbyForm.addEventListener("submit", (e) => {
    e.preventDefault();
    void runNearby(pinInput.value);
  });

  grievanceForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    grievanceError.classList.add("hidden");
    const fssaiId = gFssaiInput.value.trim();
    const issueCategory = gCategorySelect.value as GrievanceCategory;
    const incidentDate = gDateInput.value.trim();
    const orderRef = gOrderInput.value.trim() || null;
    const description = gDescInput.value.trim();
    const persist = gPersistCheckbox.checked;

    let packet: GrievancePacket;
    let sourceLabel: string;
    try {
      packet = await submitGrievancePacket(
        {
          fssai_id: fssaiId,
          issue_category: issueCategory,
          order_reference: orderRef,
          description,
          incident_date: incidentDate,
          persist,
        },
        getApiBase(),
      );
      sourceLabel = persist
        ? "Source: live API (persisted to local SQLite)"
        : "Source: Live API (india-ate serve)";
    } catch (apiErr) {
      if (apiErr instanceof Error && "status" in apiErr) {
        grievanceError.textContent = apiErr.message;
        grievanceError.classList.remove("hidden");
        return;
      }
      try {
        const receiptForGrievance =
          lastReceipt?.fssai_id === fssaiId
            ? lastReceipt
            : getFactReceiptFromSeed(fssaiId);
        packet = buildOfflineGrievancePacket({
          fssaiId,
          issueCategory,
          orderReference: orderRef,
          description,
          incidentDate,
          receipt: receiptForGrievance,
        });
        sourceLabel = persist
          ? "Source: offline packet generator (local API unreachable — NOT persisted)"
          : "Source: offline packet generator";
        if (persist) {
          grievanceError.textContent =
            "Local API is unreachable: grievance packet was built offline and NOT persisted to SQLite.";
          grievanceError.classList.remove("hidden");
        }
      } catch (offlineErr) {
        grievanceError.textContent =
          offlineErr instanceof Error
            ? offlineErr.message
            : "Failed to build grievance packet";
        grievanceError.classList.remove("hidden");
        return;
      }
    }

    grievanceOutput.innerHTML = renderGrievanceHtml(packet, sourceLabel);
    grievanceOutput.classList.remove("hidden");

    const copyBtn = document.getElementById("copy-grievance-btn");
    const copyBox = document.getElementById(
      "grievance-copy-box",
    ) as HTMLTextAreaElement | null;
    if (copyBtn && copyBox) {
      copyBtn.addEventListener("click", () => {
        void navigator.clipboard?.writeText(copyBox.value);
        copyBtn.textContent = "Copied!";
      });
    }
  });

  apiBaseInput.addEventListener("change", () => {
    void refreshHealth();
  });

  // Pre-fill from URL query ?fssai=
  const params = new URLSearchParams(window.location.search);
  const initialFssai = params.get("fssai");
  if (initialFssai) {
    fssaiInput.value = initialFssai;
    gFssaiInput.value = initialFssai;
    void runLookup(initialFssai);
  }

  if (!gDateInput.value) {
    gDateInput.value = new Date().toISOString().slice(0, 10);
  }

  void refreshHealth();
}
