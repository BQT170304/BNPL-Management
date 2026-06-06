// frontend/src/hooks/useAsync.test.tsx
import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ApiError } from "../api/client";
import { useAsync } from "./useAsync";

describe("useAsync", () => {
  it("sets data on success", async () => {
    const { result } = renderHook(() => useAsync(async (n: number) => n * 2));
    await act(async () => {
      await result.current.run(21);
    });
    expect(result.current.data).toBe(42);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("captures ApiError message", async () => {
    const { result } = renderHook(() =>
      useAsync(async () => {
        throw new ApiError(404, "nope");
      }),
    );
    await act(async () => {
      await result.current.run().catch(() => undefined);
    });
    await waitFor(() => expect(result.current.error).toBe("nope"));
  });
});
