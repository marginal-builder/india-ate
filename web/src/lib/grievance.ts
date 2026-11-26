import { decodeFssai14Offline, normalizeAndValidateFssai14 } from "./fssai";
import type { FactReceipt, GrievanceCategory, GrievancePacket } from "./types";

export const FOOD_SAFETY_CONNECT_URL =
  "https://foscos.fssai.gov.in/consumergrievance/";
export const ESCALATION_WINDOW_DAYS = 15;

export const GRIEVANCE_CATEGORIES: ReadonlyArray<{
  value: GrievanceCategory;
  label: string;
}> = [
  { value: "spoiled_food", label: "Spoiled / Contaminated Food" },
  { value: "misbranded", label: "Misbranded / Missing FSSAI Label" },
  {
    value: "shelf_life_30pct_violation",
    label: "Below 30% Remaining Shelf-Life Rule",
  },
  {
    value: "unlicensed_or_suspended",
    label: "Operating with Suspended / Invalid License",
  },
  { value: "foreign_matter", label: "Foreign Matter Found in Food" },
  { value: "other", label: "Other Food Safety Violation" },
];

function addDaysIso(isoDate: string, days: number): string {
  const match = /^([0-9]{4})-([0-9]{2})-([0-9]{2})$/.exec(isoDate.trim());
  if (!match) {
    throw new Error("incident_date must be YYYY-MM-DD");
  }
  const year = Number.parseInt(match[1], 10);
  const month = Number.parseInt(match[2], 10) - 1;
  const day = Number.parseInt(match[3], 10);
  const dt = new Date(Date.UTC(year, month, day));
  if (
    Number.isNaN(dt.getTime()) ||
    dt.getUTCFullYear() !== year ||
    dt.getUTCMonth() !== month ||
    dt.getUTCDate() !== day
  ) {
    throw new Error(`Invalid incident_date: '${isoDate}'`);
  }
  dt.setUTCDate(dt.getUTCDate() + days);
  return dt.toISOString().slice(0, 10);
}

function deterministicHexId(seed: string): string {
  // FNV-1a 64-bit style dual-lane deterministic 16-hex-char ID for offline fallback
  let h1 = 0x811c9dc5;
  let h2 = 0x9e3779b9;
  for (let i = 0; i < seed.length; i += 1) {
    const code = seed.charCodeAt(i);
    h1 ^= code;
    h1 = Math.imul(h1, 0x01000193) >>> 0;
    h2 ^= code + i;
    h2 = Math.imul(h2, 0x85ebca6b) >>> 0;
  }
  return `${h1.toString(16).padStart(8, "0")}${h2.toString(16).padStart(8, "0")}`;
}

export function buildOfflineGrievancePacket(input: {
  fssaiId: string;
  issueCategory: GrievanceCategory;
  orderReference?: string | null;
  description: string;
  incidentDate: string;
  receipt?: FactReceipt | null;
}): GrievancePacket {
  const cleanId = normalizeAndValidateFssai14(input.fssaiId);
  const decoded = decodeFssai14Offline(cleanId);
  const cleanDesc = input.description.trim();
  if (!cleanDesc) {
    throw new Error("Grievance description must be non-empty");
  }
  const cleanDate = input.incidentDate.trim();
  const escalationDeadline = addDaysIso(cleanDate, ESCALATION_WINDOW_DAYS);
  const cleanOrderRef = input.orderReference?.trim() || null;
  const seed = `${cleanId}:${input.issueCategory}:${cleanDate}:${cleanDesc}`;

  return {
    packet_id: deterministicHexId(seed),
    portal_url: FOOD_SAFETY_CONNECT_URL,
    fssai_id: cleanId,
    decoded_jurisdiction: decoded,
    premises_legal_name: input.receipt?.premises?.legal_name ?? null,
    premises_address: input.receipt?.premises?.address ?? null,
    issue_category: input.issueCategory,
    order_reference: cleanOrderRef,
    incident_date: cleanDate,
    escalation_deadline: escalationDeadline,
    description: cleanDesc,
    known_events_count: input.receipt?.events.length ?? 0,
    ticket_event: null,
  };
}
