export type VerificationTier =
  | "official_registry"
  | "peer_reviewed_science"
  | "user_verified_snapshot"
  | "synthetic_demo";

export interface EvidenceProvenance {
  source_name: string;
  source_url: string;
  retrieved_at: string;
  content_sha256: string;
  verification_tier: VerificationTier;
}

export interface RegulatoryIdentifier {
  jurisdiction_iso: string;
  scheme: string;
  raw_value: string;
}

export interface DecodedFSSAI14 {
  tier: "license" | "basic_registration";
  pre_inspection_exempt_post_apr2026: boolean;
  authority_scope: "central" | "state_or_ut";
  state_code: string;
  state_name: string;
  registration_year: number;
  officer_code: string;
  central_regional_office: string | null;
  officer_jurisdiction_state: string | null;
  serial: string;
}

export type PremisesType =
  | "cloud_kitchen"
  | "dark_store"
  | "restaurant"
  | "co_packer_factory"
  | "dairy_unit"
  | "warehouse"
  | "retail_vendor";

export interface FoodPremises {
  entity_id: string;
  legal_name: string;
  jurisdiction_iso: string;
  regulatory_ids: RegulatoryIdentifier[];
  provenance: EvidenceProvenance[];
  premises_type: PremisesType;
  address?: string | null;
  postal_code?: string | null;
  city?: string | null;
  state?: string | null;
  lat?: number | null;
  lon?: number | null;
}

export type PlatformName =
  | "swiggy"
  | "zomato"
  | "blinkit"
  | "zepto"
  | "instamart"
  | "ondc"
  | "packaged_retail";

export interface BrandListing {
  listing_id: string;
  display_name: string;
  platform: PlatformName;
  premises_entity_id: string;
  postal_code?: string | null;
  first_seen_at: string;
  last_seen_at: string;
  provenance: EvidenceProvenance;
}

export type EventType =
  | "license_status_snapshot"
  | "hygiene_audit"
  | "food_recall"
  | "enforcement_raid_or_suspension"
  | "lab_test_result"
  | "grievance_ticket";

export interface AuthoritativeEvent {
  event_id: string;
  event_type: EventType;
  target_entity_id: string;
  jurisdiction_iso: string;
  event_date: string;
  status: string;
  batch_or_lot_no?: string | null;
  verbatim_summary: string;
  provenance: EvidenceProvenance;
}

export interface FactReceipt {
  fssai_id: string;
  decoded: DecodedFSSAI14;
  premises: FoodPremises | null;
  ghost_brand_count: number;
  brand_listings: BrandListing[];
  events: AuthoritativeEvent[];
  last_verified_at: string | null;
}

export interface GhostBrandCluster {
  premises: FoodPremises;
  listings: BrandListing[];
}

export interface VerifiedSwitchOption {
  premises: FoodPremises;
  verification_reasons: string[];
  hygiene_events: AuthoritativeEvent[];
}

export type GrievanceCategory =
  | "spoiled_food"
  | "misbranded"
  | "shelf_life_30pct_violation"
  | "unlicensed_or_suspended"
  | "foreign_matter"
  | "other";

export interface GrievancePacket {
  packet_id: string;
  portal_url: string;
  fssai_id: string;
  decoded_jurisdiction: DecodedFSSAI14;
  premises_legal_name: string | null;
  premises_address: string | null;
  issue_category: GrievanceCategory;
  order_reference: string | null;
  incident_date: string;
  escalation_deadline: string;
  description: string;
  known_events_count: number;
  ticket_event?: AuthoritativeEvent | null;
}

export interface DarkStoreEntry {
  slug: string;
  platform: PlatformName;
  storefront_label: string;
  fssai_id: string;
}
