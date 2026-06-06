// frontend/src/features/ingestion/CifImport.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CifSeed } from "../../api/types";
import { CifImport } from "./CifImport";

afterEach(() => vi.restoreAllMocks());

describe("CifImport", () => {
  it("fetches the default CIF 10000327 seed and emits it", async () => {
    const seed: CifSeed = { cif: "10000327", income: 12_000_000, expense: 5_000_000, debt_payment: 2_000_000 };
    const spy = vi.fn(async (_url: string) => new Response(JSON.stringify(seed), { status: 200 }));
    vi.stubGlobal("fetch", spy);
    const onSeed = vi.fn();

    render(<CifImport onSeed={onSeed} />);
    await userEvent.click(screen.getByRole("button", { name: /dùng dữ liệu/i }));

    await waitFor(() => expect(onSeed).toHaveBeenCalledWith(seed));
    expect(spy.mock.calls[0][0]).toContain("/ingestion/cif/10000327/seed");
  });
});
