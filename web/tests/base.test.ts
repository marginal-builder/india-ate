import { describe, expect, it } from "vitest";
import { joinBase } from "../src/lib/base";

describe("joinBase", () => {
  it("keeps root paths clean", () => {
    expect(joinBase("/", "/")).toBe("/");
    expect(joinBase("/", "/in/license/1")).toBe("/in/license/1");
    expect(joinBase("/", "/#grievance")).toBe("/#grievance");
  });

  it("prefixes GitHub Pages project paths", () => {
    expect(joinBase("/india-ate/", "/")).toBe("/india-ate/");
    expect(joinBase("/india-ate/", "/in/pincode/560034")).toBe(
      "/india-ate/in/pincode/560034",
    );
    expect(joinBase("/india-ate/", "in/license/1")).toBe(
      "/india-ate/in/license/1",
    );
  });

  it("normalizes a base without a trailing slash", () => {
    expect(joinBase("/india-ate", "/in/license/1")).toBe(
      "/india-ate/in/license/1",
    );
  });
});
