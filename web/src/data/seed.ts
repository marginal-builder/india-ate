import { decodeFssai14Offline } from "../lib/fssai";
import type {
  AuthoritativeEvent,
  BrandListing,
  DarkStoreEntry,
  EvidenceProvenance,
  FactReceipt,
  FoodPremises,
  VerifiedSwitchOption,
} from "../lib/types";

// Synthetic demo fixtures only. These records are illustrative, must never be
// treated as official FSSAI/FoSCoS data, and are not used by the backend.
// The all-zero hash intentionally signals that no real snapshot exists.
const DEMO_HASH =
  "0000000000000000000000000000000000000000000000000000000000000000";
const DEMO_SOURCE_URL = "https://example.com/india-ate/synthetic-demo";

const PROV_DEMO_REGISTRY: EvidenceProvenance = {
  source_name: "Synthetic demo fixture — registry",
  source_url: DEMO_SOURCE_URL,
  retrieved_at: "2026-04-12T09:30:00Z",
  content_sha256: DEMO_HASH,
  verification_tier: "synthetic_demo",
};

const PROV_DEMO_HYGIENE: EvidenceProvenance = {
  source_name: "Synthetic demo fixture — hygiene audit",
  source_url: DEMO_SOURCE_URL,
  retrieved_at: "2026-04-10T11:15:00Z",
  content_sha256: DEMO_HASH,
  verification_tier: "synthetic_demo",
};

const PROV_DEMO_ENFORCEMENT: EvidenceProvenance = {
  source_name: "Synthetic demo fixture — enforcement",
  source_url: DEMO_SOURCE_URL,
  retrieved_at: "2026-04-14T14:20:00Z",
  content_sha256: DEMO_HASH,
  verification_tier: "synthetic_demo",
};

const PROV_DEMO_CATALOG: EvidenceProvenance = {
  source_name: "Synthetic demo fixture — catalog",
  source_url: DEMO_SOURCE_URL,
  retrieved_at: "2026-04-11T08:45:00Z",
  content_sha256: DEMO_HASH,
  verification_tier: "synthetic_demo",
};

export const SEED_PREMISES: FoodPremises[] = [
  {
    entity_id: "actor:in:fssai:21226001000412",
    legal_name: "Demo Multi-Brand Kitchens (Synthetic)",
    jurisdiction_iso: "IN",
    regulatory_ids: [
      {
        jurisdiction_iso: "IN",
        scheme: "IN_FSSAI_14",
        raw_value: "21226001000412",
      },
    ],
    provenance: [PROV_DEMO_REGISTRY],
    premises_type: "cloud_kitchen",
    address: "2nd Floor, 80 Feet Road, Koramangala 4th Block",
    postal_code: "560034",
    city: "Bengaluru",
    state: "Karnataka",
  },
  {
    entity_id: "actor:in:fssai:11223302000845",
    legal_name: "Demo Heritage Kitchen (Synthetic)",
    jurisdiction_iso: "IN",
    regulatory_ids: [
      {
        jurisdiction_iso: "IN",
        scheme: "IN_FSSAI_14",
        raw_value: "11223302000845",
      },
    ],
    provenance: [PROV_DEMO_HYGIENE],
    premises_type: "restaurant",
    address: "17th Main Road, Koramangala 6th Block",
    postal_code: "560034",
    city: "Bengaluru",
    state: "Karnataka",
  },
  {
    entity_id: "actor:in:fssai:11224302001190",
    legal_name: "Demo Quick Logistics Hub (Synthetic)",
    jurisdiction_iso: "IN",
    regulatory_ids: [
      {
        jurisdiction_iso: "IN",
        scheme: "IN_FSSAI_14",
        raw_value: "11224302001190",
      },
    ],
    provenance: [PROV_DEMO_ENFORCEMENT],
    premises_type: "dark_store",
    address: "Ground Floor, 100 Feet Ring Road, Koramangala 1st Block",
    postal_code: "560034",
    city: "Bengaluru",
    state: "Karnataka",
  },
  {
    entity_id: "actor:in:fssai:13624001000999",
    legal_name: "Demo Verified Kitchen (Synthetic)",
    jurisdiction_iso: "IN",
    regulatory_ids: [
      {
        jurisdiction_iso: "IN",
        scheme: "IN_FSSAI_14",
        raw_value: "13624001000999",
      },
    ],
    provenance: [PROV_DEMO_HYGIENE],
    premises_type: "restaurant",
    address: "Plot 44, Hitech City Main Road, Madhapur",
    postal_code: "500081",
    city: "Hyderabad",
    state: "Telangana",
  },
  {
    entity_id: "actor:in:fssai:11525015002310",
    legal_name: "Demo Cold-Chain Hub (Synthetic)",
    jurisdiction_iso: "IN",
    regulatory_ids: [
      {
        jurisdiction_iso: "IN",
        scheme: "IN_FSSAI_14",
        raw_value: "11525015002310",
      },
    ],
    provenance: [PROV_DEMO_REGISTRY],
    premises_type: "dark_store",
    address: "Unit 3, Chapel Road, Bandra West",
    postal_code: "400050",
    city: "Mumbai",
    state: "Maharashtra",
  },
  {
    entity_id: "actor:in:fssai:13321999000712",
    legal_name: "Demo Rapid Fulfilment Unit (Synthetic)",
    jurisdiction_iso: "IN",
    regulatory_ids: [
      {
        jurisdiction_iso: "IN",
        scheme: "IN_FSSAI_14",
        raw_value: "13321999000712",
      },
    ],
    provenance: [PROV_DEMO_REGISTRY],
    premises_type: "dark_store",
    address: "Block M, Outer Circle, Connaught Place",
    postal_code: "110001",
    city: "New Delhi",
    state: "Delhi",
  },
];

export const SEED_BRAND_LISTINGS: BrandListing[] = [
  {
    listing_id: "listing:swiggy:bowl-express-560034",
    display_name: "Demo Bowl Express",
    platform: "swiggy",
    premises_entity_id: "actor:in:fssai:21226001000412",
    postal_code: "560034",
    first_seen_at: "2026-04-02T10:00:00Z",
    last_seen_at: "2026-04-12T10:00:00Z",
    provenance: PROV_DEMO_CATALOG,
  },
  {
    listing_id: "listing:zomato:tandoor-nights-560034",
    display_name: "Demo Tandoor Nights",
    platform: "zomato",
    premises_entity_id: "actor:in:fssai:21226001000412",
    postal_code: "560034",
    first_seen_at: "2026-04-03T10:00:00Z",
    last_seen_at: "2026-04-12T10:00:00Z",
    provenance: PROV_DEMO_CATALOG,
  },
  {
    listing_id: "listing:swiggy:wok-and-roll-560034",
    display_name: "Demo Wok & Roll",
    platform: "swiggy",
    premises_entity_id: "actor:in:fssai:21226001000412",
    postal_code: "560034",
    first_seen_at: "2026-04-04T10:00:00Z",
    last_seen_at: "2026-04-12T10:00:00Z",
    provenance: PROV_DEMO_CATALOG,
  },
  {
    listing_id: "listing:ondc:midnight-biryani-560034",
    display_name: "Demo Midnight Biryani",
    platform: "ondc",
    premises_entity_id: "actor:in:fssai:21226001000412",
    postal_code: "560034",
    first_seen_at: "2026-04-05T10:00:00Z",
    last_seen_at: "2026-04-12T10:00:00Z",
    provenance: PROV_DEMO_CATALOG,
  },
  {
    listing_id: "listing:ondc:dakshin-heritage-560034",
    display_name: "Demo Heritage Kitchen",
    platform: "ondc",
    premises_entity_id: "actor:in:fssai:11223302000845",
    postal_code: "560034",
    first_seen_at: "2026-03-15T10:00:00Z",
    last_seen_at: "2026-04-10T10:00:00Z",
    provenance: PROV_DEMO_CATALOG,
  },
  {
    listing_id: "listing:blinkit:koramangala-560034",
    display_name: "Demo Dark Store — Koramangala",
    platform: "blinkit",
    premises_entity_id: "actor:in:fssai:11224302001190",
    postal_code: "560034",
    first_seen_at: "2026-02-01T10:00:00Z",
    last_seen_at: "2026-04-14T10:00:00Z",
    provenance: PROV_DEMO_REGISTRY,
  },
  {
    listing_id: "listing:ondc:spice-route-500081",
    display_name: "Demo Spice Route",
    platform: "ondc",
    premises_entity_id: "actor:in:fssai:13624001000999",
    postal_code: "500081",
    first_seen_at: "2026-03-01T10:00:00Z",
    last_seen_at: "2026-04-01T10:00:00Z",
    provenance: PROV_DEMO_CATALOG,
  },
  {
    listing_id: "listing:zepto:bandra-west-400050",
    display_name: "Demo Dark Store — Bandra West",
    platform: "zepto",
    premises_entity_id: "actor:in:fssai:11525015002310",
    postal_code: "400050",
    first_seen_at: "2026-03-20T10:00:00Z",
    last_seen_at: "2026-04-12T10:00:00Z",
    provenance: PROV_DEMO_REGISTRY,
  },
  {
    listing_id: "listing:instamart:connaught-place-110001",
    display_name: "Demo Dark Store — Connaught Place",
    platform: "instamart",
    premises_entity_id: "actor:in:fssai:13321999000712",
    postal_code: "110001",
    first_seen_at: "2026-03-18T10:00:00Z",
    last_seen_at: "2026-04-12T10:00:00Z",
    provenance: PROV_DEMO_REGISTRY,
  },
];

export const SEED_EVENTS: AuthoritativeEvent[] = [
  {
    event_id: "evt:license:21226001000412:2026-04-12",
    event_type: "license_status_snapshot",
    target_entity_id: "actor:in:fssai:21226001000412",
    jurisdiction_iso: "IN",
    event_date: "2026-04-12",
    status: "Active (Basic Registration)",
    verbatim_summary:
      "Synthetic demo record: Basic Registration active; post-April 1, 2026 threshold up to Rs 1.5 Cr with no pre-inspection.",
    provenance: PROV_DEMO_REGISTRY,
  },
  {
    event_id: "evt:hygiene:11223302000845:2026-03-28",
    event_type: "hygiene_audit",
    target_entity_id: "actor:in:fssai:11223302000845",
    jurisdiction_iso: "IN",
    event_date: "2026-03-28",
    status: "4/5",
    verbatim_summary:
      "Synthetic demo record: Hygiene Rating 4/5 completed by an empanelled audit agency.",
    provenance: PROV_DEMO_HYGIENE,
  },
  {
    event_id: "evt:raid:11224302001190:2026-04-14",
    event_type: "enforcement_raid_or_suspension",
    target_entity_id: "actor:in:fssai:11224302001190",
    jurisdiction_iso: "IN",
    event_date: "2026-04-14",
    status: "Suspended",
    verbatim_summary:
      "Synthetic demo record: state inspection observed cold-chain and expired-stock non-compliance; license status listed as Suspended.",
    provenance: PROV_DEMO_ENFORCEMENT,
  },
  {
    event_id: "evt:hygiene:13624001000999:2026-03-01",
    event_type: "hygiene_audit",
    target_entity_id: "actor:in:fssai:13624001000999",
    jurisdiction_iso: "IN",
    event_date: "2026-03-01",
    status: "5/5",
    verbatim_summary: "Synthetic demo record: Hygiene Rating 5/5 completed.",
    provenance: PROV_DEMO_HYGIENE,
  },
  {
    event_id: "evt:license:11525015002310:2026-04-12",
    event_type: "license_status_snapshot",
    target_entity_id: "actor:in:fssai:11525015002310",
    jurisdiction_iso: "IN",
    event_date: "2026-04-12",
    status: "Active",
    verbatim_summary: "Synthetic demo record: State License Active.",
    provenance: PROV_DEMO_REGISTRY,
  },
  {
    event_id: "evt:license:13321999000712:2026-04-12",
    event_type: "license_status_snapshot",
    target_entity_id: "actor:in:fssai:13321999000712",
    jurisdiction_iso: "IN",
    event_date: "2026-04-12",
    status: "Active",
    verbatim_summary: "Synthetic demo record: State License Active.",
    provenance: PROV_DEMO_REGISTRY,
  },
];

export const SEED_DARK_STORES: DarkStoreEntry[] = [
  {
    slug: "demo-dark-store-koramangala-560034",
    platform: "blinkit",
    storefront_label: "Demo Dark Store — Koramangala",
    fssai_id: "11224302001190",
  },
  {
    slug: "demo-dark-store-bandra-west-400050",
    platform: "zepto",
    storefront_label: "Demo Dark Store — Bandra West",
    fssai_id: "11525015002310",
  },
  {
    slug: "demo-dark-store-connaught-place-110001",
    platform: "instamart",
    storefront_label: "Demo Dark Store — Connaught Place",
    fssai_id: "13321999000712",
  },
];

const NEGATIVE_EVENT_TYPES = new Set([
  "food_recall",
  "enforcement_raid_or_suspension",
]);

export function getFssaiIdFromPremises(premises: FoodPremises): string | null {
  const reg = premises.regulatory_ids.find((r) => r.scheme === "IN_FSSAI_14");
  return reg ? reg.raw_value.trim() : null;
}

export function getAllLicenseIds(): string[] {
  return SEED_PREMISES.map(getFssaiIdFromPremises).filter(
    (id): id is string => Boolean(id),
  );
}

export function getAllPincodes(): string[] {
  const pins = new Set<string>();
  for (const p of SEED_PREMISES) {
    if (p.postal_code) {
      pins.add(p.postal_code);
    }
  }
  return Array.from(pins).sort();
}

export function getDarkStoreBySlug(slug: string): DarkStoreEntry | null {
  return SEED_DARK_STORES.find((d) => d.slug === slug) ?? null;
}

export function getFactReceiptFromSeed(fssaiId: string): FactReceipt {
  const cleanId = fssaiId.trim();
  const decoded = decodeFssai14Offline(cleanId);
  const premises =
    SEED_PREMISES.find((p) => getFssaiIdFromPremises(p) === cleanId) ?? null;
  if (!premises) {
    return {
      fssai_id: cleanId,
      decoded,
      premises: null,
      ghost_brand_count: 0,
      brand_listings: [],
      events: [],
      last_verified_at: null,
    };
  }
  const listings = SEED_BRAND_LISTINGS.filter(
    (l) => l.premises_entity_id === premises.entity_id,
  );
  const events = SEED_EVENTS.filter(
    (e) => e.target_entity_id === premises.entity_id,
  ).sort((a, b) => b.event_date.localeCompare(a.event_date));

  const timestamps = [
    ...premises.provenance.map((p) => p.retrieved_at),
    ...events.map((e) => e.provenance.retrieved_at),
  ].sort();

  return {
    fssai_id: cleanId,
    decoded,
    premises,
    ghost_brand_count: listings.length,
    brand_listings: listings,
    events,
    last_verified_at:
      timestamps.length > 0 ? timestamps[timestamps.length - 1] : null,
  };
}

export function getPremisesByPincodeFromSeed(
  postalCode: string,
): FactReceipt[] {
  const cleanPin = postalCode.trim();
  return SEED_PREMISES.filter((p) => p.postal_code === cleanPin)
    .map((p) => getFssaiIdFromPremises(p))
    .filter((id): id is string => Boolean(id))
    .map((id) => getFactReceiptFromSeed(id));
}

export function getVerifiedNearbyFromSeed(
  postalCode: string,
): VerifiedSwitchOption[] {
  const cleanPin = postalCode.trim();
  const candidates = SEED_PREMISES.filter((p) => p.postal_code === cleanPin);
  const options: VerifiedSwitchOption[] = [];

  for (const premises of candidates) {
    const events = SEED_EVENTS.filter(
      (e) => e.target_entity_id === premises.entity_id,
    );
    if (events.some((e) => NEGATIVE_EVENT_TYPES.has(e.event_type))) {
      continue;
    }
    const hygieneEvents = events.filter(
      (e) => e.event_type === "hygiene_audit",
    );
    const reasons = hygieneEvents.map(
      (e) => `Completed FSSAI Hygiene Audit (${e.status})`,
    );
    const hasTier1 = premises.regulatory_ids.some(
      (r) => r.scheme === "IN_FSSAI_14" && r.raw_value.trim().startsWith("1"),
    );
    if (hasTier1) {
      reasons.push("State/Central Tier-1 License");
    }
    if (reasons.length > 0) {
      options.push({
        premises,
        verification_reasons: reasons,
        hygiene_events: hygieneEvents,
      });
    }
  }
  return options;
}
