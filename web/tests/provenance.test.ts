import { describe, expect, it } from "vitest";
import { getFactReceiptFromSeed } from "../src/data/seed";
import {
  receiptUsesSyntheticData,
  verificationTierLabel,
} from "../src/lib/provenance";
import type { FactReceipt } from "../src/lib/types";

describe("provenance helpers", () => {
  it("labels every supported verification tier", () => {
    expect(verificationTierLabel("official_registry")).toBe("Official registry");
    expect(verificationTierLabel("peer_reviewed_science")).toBe(
      "Peer-reviewed science",
    );
    expect(verificationTierLabel("user_verified_snapshot")).toBe(
      "User-submitted snapshot",
    );
    expect(verificationTierLabel("synthetic_demo")).toBe("Synthetic demo");
  });

  it("detects the synthetic demo seed and official-only receipts", () => {
    expect(receiptUsesSyntheticData(getFactReceiptFromSeed("21226001000412"))).toBe(
      true,
    );

    const officialOnly: FactReceipt = {
      fssai_id: "10013022000417",
      decoded: getFactReceiptFromSeed("10013022000417").decoded,
      premises: null,
      ghost_brand_count: 0,
      brand_listings: [],
      events: [],
      last_verified_at: null,
    };
    expect(receiptUsesSyntheticData(officialOnly)).toBe(false);
  });
});
