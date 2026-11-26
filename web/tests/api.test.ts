import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  checkApiHealth,
  fetchDecode,
  fetchFactReceipt,
  fetchGhostCluster,
  fetchVerifiedNearby,
  submitGrievancePacket,
} from "../src/lib/api";

afterEach(() => {
  vi.restoreAllMocks();
});

function mockJsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api client", () => {
  it("checkApiHealth returns true on { status: 'ok' } and false on network failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(mockJsonResponse({ status: "ok" })),
    );
    expect(await checkApiHealth("http://127.0.0.1:8000")).toBe(true);

    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValueOnce(new TypeError("Connection refused")),
    );
    expect(await checkApiHealth("http://127.0.0.1:8000")).toBe(false);
  });

  it("calls decode, receipt, cluster, and nearby endpoints with encoded IDs", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(mockJsonResponse({ tier: "license" }))
      .mockResolvedValueOnce(mockJsonResponse({ fssai_id: "10013022000417" }))
      .mockResolvedValueOnce(mockJsonResponse({ listings: [] }))
      .mockResolvedValueOnce(
        mockJsonResponse({ postal_code: "560034", options: [] }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await fetchDecode(" 10013022000417 ", "http://127.0.0.1:8000");
    await fetchFactReceipt("10013022000417", "http://127.0.0.1:8000");
    await fetchGhostCluster("10013022000417", "http://127.0.0.1:8000");
    await fetchVerifiedNearby(" 560034 ", "http://127.0.0.1:8000");

    expect(fetchMock.mock.calls[0][0]).toBe(
      "http://127.0.0.1:8000/v1/decode/10013022000417",
    );
    expect(fetchMock.mock.calls[1][0]).toBe(
      "http://127.0.0.1:8000/v1/receipt/10013022000417",
    );
    expect(fetchMock.mock.calls[2][0]).toBe(
      "http://127.0.0.1:8000/v1/cluster/10013022000417",
    );
    expect(fetchMock.mock.calls[3][0]).toBe(
      "http://127.0.0.1:8000/v1/nearby/560034",
    );
  });

  it("throws ApiError with backend error message on HTTP 400", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(
          mockJsonResponse({ error: "Grievance description must be non-empty" }, 400),
        ),
    );

    await expect(
      submitGrievancePacket({
        fssai_id: "21226001000412",
        issue_category: "spoiled_food",
        description: "",
        incident_date: "2026-04-20",
      }),
    ).rejects.toMatchObject({
      name: "Error",
      status: 400,
      message: "Grievance description must be non-empty",
    });
  });

  it("wraps non-JSON error responses in ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce(
        new Response("<html>Bad gateway</html>", {
          status: 502,
          headers: { "Content-Type": "text/html" },
        }),
      ),
    );

    await expect(fetchDecode("10013022000417")).rejects.toMatchObject({
      status: 502,
      message: "HTTP 502",
    });
  });

  it("ApiError preserves HTTP status code", () => {
    const err = new ApiError(404, "Premises not found");
    expect(err.status).toBe(404);
    expect(err.message).toBe("Premises not found");
  });
});
