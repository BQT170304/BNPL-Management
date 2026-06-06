// frontend/src/features/profile/ProfileBuilder.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ActiveProfileProvider } from "../../state/activeProfile";
import { ProfileBuilder } from "./ProfileBuilder";

afterEach(() => vi.restoreAllMocks());

describe("ProfileBuilder", () => {
  it("submits a profile and reports success", async () => {
    const spy = vi.fn(async (_url: string, _init?: RequestInit) =>
      new Response(JSON.stringify({ id: "p-1-x" }), { status: 201 }),
    );
    vi.stubGlobal("fetch", spy);
    const onSaved = vi.fn();

    render(
      <ActiveProfileProvider>
        <ProfileBuilder initialSeed={null} onSaved={onSaved} />
      </ActiveProfileProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: /tạo hồ sơ/i }));

    await waitFor(() => expect(spy).toHaveBeenCalled());
    const [url, init] = spy.mock.calls[0];
    expect(url).toBe("/api/profiles");
    expect((init as RequestInit).method).toBe("POST");
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
  });
});
