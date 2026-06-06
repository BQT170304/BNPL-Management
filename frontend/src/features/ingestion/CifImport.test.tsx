// frontend/src/features/ingestion/CifImport.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CifSeed } from "../../api/types";
import { CifImport } from "./CifImport";

afterEach(() => vi.restoreAllMocks());

describe("CifImport", () => {
  it("lists CIFs and emits a seed on selection", async () => {
    const seed: CifSeed = { cif: "100", income: 12_000_000, expense: 5_000_000, debt_payment: 2_000_000 };
    vi.stubGlobal("fetch", vi.fn(async (url: string) => {
      if (url.includes("/ingestion/cifs")) {
        return new Response(JSON.stringify({ cifs: ["100", "200"] }), { status: 200 });
      }
      return new Response(JSON.stringify(seed), { status: 200 });
    }));
    const onSeed = vi.fn();

    render(<CifImport onSeed={onSeed} />);
    await waitFor(() => expect(screen.getByRole("option", { name: "100" })).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /dùng dữ liệu/i }));
    await waitFor(() => expect(onSeed).toHaveBeenCalledWith(seed));
  });
});
