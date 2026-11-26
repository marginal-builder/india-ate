import { describe, expect, it } from "vitest";
import {
  FOOD_SAFETY_CONNECT_URL,
  buildOfflineGrievancePacket,
} from "../src/lib/grievance";

describe("buildOfflineGrievancePacket", () => {
  it("computes 15-day escalation deadline across month boundary", () => {
    const packet = buildOfflineGrievancePacket({
      fssaiId: "13624001000999",
      issueCategory: "shelf_life_30pct_violation",
      orderReference: "ORD-42",
      description: "Delivered with 10% remaining shelf life.",
      incidentDate: "2026-04-20",
    });
    expect(packet.portal_url).toBe(FOOD_SAFETY_CONNECT_URL);
    expect(packet.escalation_deadline).toBe("2026-05-05");
    expect(packet.order_reference).toBe("ORD-42");
    expect(packet.decoded_jurisdiction.state_name).toBe("Telangana");
  });

  it("rejects empty description, bad date, or invalid FSSAI ID", () => {
    expect(() =>
      buildOfflineGrievancePacket({
        fssaiId: "13624001000999",
        issueCategory: "spoiled_food",
        description: "   ",
        incidentDate: "2026-04-01",
      }),
    ).toThrow(/non-empty/);

    expect(() =>
      buildOfflineGrievancePacket({
        fssaiId: "13624001000999",
        issueCategory: "spoiled_food",
        description: "Spoiled",
        incidentDate: "2026-02-31",
      }),
    ).toThrow(/Invalid incident_date/);

    expect(() =>
      buildOfflineGrievancePacket({
        fssaiId: "bad",
        issueCategory: "spoiled_food",
        description: "Spoiled",
        incidentDate: "2026-04-01",
      }),
    ).toThrow(/14-digit/);
  });
});
