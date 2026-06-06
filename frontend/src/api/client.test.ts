// frontend/src/api/client.test.ts
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "./client";

afterEach(() => vi.restoreAllMocks());

function mockFetch(status: number, body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
}

describe("apiFetch", () => {
  it("returns parsed JSON on 200", async () => {
    mockFetch(200, { id: "p1" });
    const data = await apiFetch<{ id: string }>("/profiles");
    expect(data).toEqual({ id: "p1" });
  });

  it("prefixes /api and passes method/body", async () => {
    const spy = vi.fn(async () => new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", spy);
    await apiFetch("/profiles", { method: "POST", body: JSON.stringify({ a: 1 }) });
    expect(spy).toHaveBeenCalledWith(
      "/api/profiles",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws ApiError with detail on non-2xx", async () => {
    mockFetch(404, { detail: "Profile not found: p1" });
    await expect(apiFetch("/profiles/p1/analysis")).rejects.toMatchObject({
      status: 404,
      detail: "Profile not found: p1",
    });
  });

  it("ApiError is an Error", async () => {
    const err = new ApiError(400, "bad");
    expect(err).toBeInstanceOf(Error);
    expect(err.message).toContain("bad");
  });
});
