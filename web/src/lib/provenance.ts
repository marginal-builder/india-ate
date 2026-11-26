import type { FactReceipt, VerificationTier } from "./types";

const TIER_LABELS: Record<VerificationTier, string> = {
  official_registry: "Official registry",
  peer_reviewed_science: "Peer-reviewed science",
  user_verified_snapshot: "User-submitted snapshot",
  synthetic_demo: "Synthetic demo",
};

export function verificationTierLabel(tier: VerificationTier): string {
  return TIER_LABELS[tier];
}

export function receiptUsesSyntheticData(receipt: FactReceipt): boolean {
  const provenances = [
    ...(receipt.premises?.provenance ?? []),
    ...receipt.brand_listings.map((listing) => listing.provenance),
    ...receipt.events.map((event) => event.provenance),
  ];
  return provenances.some(
    (provenance) => provenance.verification_tier === "synthetic_demo",
  );
}
