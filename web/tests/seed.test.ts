import { describe, expect, it } from "vitest";
import {
  SEED_BRAND_LISTINGS,
  SEED_DARK_STORES,
  SEED_EVENTS,
  SEED_PREMISES,
  getAllLicenseIds,
  getAllPincodes,
  getFactReceiptFromSeed,
  getVerifiedNearbyFromSeed,
} from "../src/data/seed";
import { decodeFssai14Offline } from "../src/lib/fssai";

describe("seed dataset & programmatic SEO invariants", () => {
  it("decodes every seeded FSSAI ID deterministically", () => {
    const ids = getAllLicenseIds();
    expect(ids.length).toBe(SEED_PREMISES.length);
    for (const id of ids) {
      expect(() => decodeFssai14Offline(id)).not.toThrow();
    }
  });

  it("exposes ghost-brand cluster count for multi-brand cloud kitchen", () => {
    const receipt = getFactReceiptFromSeed("21226001000412");
    expect(receipt.ghost_brand_count).toBe(4);
    expect(receipt.decoded.pre_inspection_exempt_post_apr2026).toBe(true);
    expect(receipt.last_verified_at).toBeTruthy();
  });

  it("excludes suspended dark store from nearby options in 560034", () => {
    const options = getVerifiedNearbyFromSeed("560034");
    const ids = options.map(
      (o) =>
        o.premises.regulatory_ids.find((r) => r.scheme === "IN_FSSAI_14")
          ?.raw_value,
    );
    expect(ids).toContain("11223302000845");
    expect(ids).not.toContain("11224302001190");
  });

  it("labels every fixture as synthetic demo data", () => {
    for (const p of SEED_PREMISES) {
      expect(p.provenance.length).toBeGreaterThan(0);
      for (const prov of p.provenance) {
        expect(prov.source_url).toMatch(/^https:\/\//);
        expect(prov.content_sha256.length).toBe(64);
        expect(prov.verification_tier).toBe("synthetic_demo");
        expect(prov.source_name.toLowerCase()).toContain("synthetic demo");
      }
    }
    for (const l of SEED_BRAND_LISTINGS) {
      expect(l.provenance.source_url).toMatch(/^https:\/\//);
      expect(l.provenance.verification_tier).toBe("synthetic_demo");
    }
    for (const e of SEED_EVENTS) {
      expect(e.provenance.source_url).toMatch(/^https:\/\//);
      expect(e.provenance.verification_tier).toBe("synthetic_demo");
    }
    expect(getAllPincodes()).toContain("560034");
    expect(SEED_DARK_STORES.length).toBe(3);
  });
});
