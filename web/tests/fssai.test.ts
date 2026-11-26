import { describe, expect, it } from "vitest";
import {
  decodeFssai14Offline,
  describeLicenseTierFact,
} from "../src/lib/fssai";

describe("decodeFssai14Offline", () => {
  it("decodes a Tier-1 Central License with RO/DO mapping", () => {
    const res = decodeFssai14Offline(" 10013022000417 ");
    expect(res).toEqual({
      tier: "license",
      pre_inspection_exempt_post_apr2026: false,
      authority_scope: "central",
      state_code: "00",
      state_name: "Central",
      registration_year: 2013,
      officer_code: "022",
      central_regional_office: "RO Mumbai",
      officer_jurisdiction_state: "Maharashtra",
      serial: "000417",
    });
  });

  it("decodes a Tier-2 Basic Registration and flags post-April 2026 rule", () => {
    const res = decodeFssai14Offline("21226001000412");
    expect(res.tier).toBe("basic_registration");
    expect(res.pre_inspection_exempt_post_apr2026).toBe(true);
    expect(res.state_name).toBe("Karnataka");
    expect(res.registration_year).toBe(2026);
    expect(describeLicenseTierFact(res)).toContain("no pre-inspection");
  });

  it("rejects malformed, non-numeric, invalid-tier, and unknown-state IDs", () => {
    expect(() => decodeFssai14Offline("123")).toThrow(/14-digit/);
    expect(() => decodeFssai14Offline("1001302200041a")).toThrow(/14-digit/);
    expect(() => decodeFssai14Offline("30013022000417")).toThrow(/tier digit/);
    expect(() => decodeFssai14Offline("19913022000417")).toThrow(/state or UT/);
  });
});
