import { describe, expect, it } from "vitest";
import {
  getFactReceiptFromSeed,
  getVerifiedNearbyFromSeed,
} from "../src/data/seed";
import { decodeFssai14Offline } from "../src/lib/fssai";
import { buildOfflineGrievancePacket } from "../src/lib/grievance";
import type { FactReceipt } from "../src/lib/types";
import {
  renderGrievanceHtml,
  renderNearbyHtml,
  renderReceiptHtml,
} from "../src/scripts/consumer-ui";

describe("consumer-ui HTML renderers", () => {
  it("renders Central Regional Office, batch/lot, sha256, and sanitizes unsafe URLs", () => {
    const centralReceipt: FactReceipt = {
      fssai_id: "10013022000417",
      decoded: decodeFssai14Offline("10013022000417"),
      premises: null,
      ghost_brand_count: 1,
      brand_listings: [
        {
          listing_id: "l1",
          display_name: "Test <script>alert(1)</script> Brand",
          platform: "ondc",
          premises_entity_id: "actor:in:fssai:10013022000417",
          postal_code: "400001",
          first_seen_at: "2026-04-01T00:00:00Z",
          last_seen_at: "2026-04-12T00:00:00Z",
          provenance: {
            source_name: "Untrusted Link",
            source_url: "javascript:alert(1)",
            retrieved_at: "2026-04-12T00:00:00Z",
            content_sha256: "abcdef1234567890",
            verification_tier: "user_verified_snapshot",
          },
        },
      ],
      events: [
        {
          event_id: "e1",
          event_type: "food_recall",
          target_entity_id: "actor:in:fssai:10013022000417",
          jurisdiction_iso: "IN",
          event_date: "2026-04-10",
          status: "Recalled",
          batch_or_lot_no: "LOT-991",
          verbatim_summary: "Recall notice issued.",
          provenance: {
            source_name: "FoSCoS Recall Portal",
            source_url: "https://foscos.fssai.gov.in/",
            retrieved_at: "2026-04-10T00:00:00Z",
            content_sha256: "1234567890abcdef",
            verification_tier: "official_registry",
          },
        },
      ],
      last_verified_at: "2026-04-12T00:00:00Z",
    };

    const html = renderReceiptHtml(centralReceipt, "Source: Test");
    expect(html).toContain("RO Mumbai (Maharashtra)");
    expect(html).toContain("Batch/Lot: LOT-991");
    expect(html).toContain("sha256: 1234567890ab");
    expect(html).not.toContain("<script>");
    expect(html).toContain("&lt;script&gt;alert(1)&lt;/script&gt;");
    expect(html).not.toContain("javascript:alert(1)");
    expect(html).toContain('href="#"');
  });

  it("labels an empty synthetic nearby result as illustrative", () => {
    const html = renderNearbyHtml(
      "999999",
      [],
      "Source: synthetic demo fixtures",
    );
    expect(html).toContain("No illustrative nearby switch options");
  });

  it("renders seed receipt, nearby switch, and grievance packet without subjective grades", () => {
    const receipt = getFactReceiptFromSeed("21226001000412");
    const receiptHtml = renderReceiptHtml(
      receipt,
      "Source: synthetic demo fixtures",
    );
    expect(receiptHtml).toContain("Synthetic demo — not an official record");
    expect(receiptHtml).toContain("Illustrative data only");
    expect(receiptHtml).toContain("no pre-inspection");
    expect(receiptHtml).toContain("Illustrative Ghost-Brand Cluster (4)");
    expect(receiptHtml).toContain("Illustrative Records (Synthetic Demo)");
    expect(receiptHtml).not.toContain("Official Authoritative Records");

    const nearby = getVerifiedNearbyFromSeed("560034");
    const nearbyHtml = renderNearbyHtml(
      "560034",
      nearby,
      "Source: synthetic demo fixtures",
    );
    expect(nearbyHtml).toContain("Demo Heritage Kitchen (Synthetic)");
    expect(nearbyHtml).not.toContain("Demo Quick Logistics Hub (Synthetic)");

    const packet = buildOfflineGrievancePacket({
      fssaiId: "21226001000412",
      issueCategory: "spoiled_food",
      description: "Spoiled meal delivered",
      incidentDate: "2026-04-20",
      receipt,
    });
    const grievanceHtml = renderGrievanceHtml(packet, "Source: offline");
    expect(grievanceHtml).toContain("2026-05-05");
    expect(grievanceHtml).toContain("Demo Multi-Brand Kitchens (Synthetic)");
    expect(grievanceHtml).toContain("Known Sourced Events");
    expect(grievanceHtml).toContain("https://foscos.fssai.gov.in/consumergrievance/");
  });
});
