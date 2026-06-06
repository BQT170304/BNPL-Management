import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./auth";

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

function Probe() {
  const { token, login } = useAuth();
  return (
    <div>
      <span data-testid="token">{token ?? "none"}</span>
      <button onClick={() => login("nguyenvana", "123456").catch(() => undefined)}>
        do-login
      </button>
    </div>
  );
}

describe("AuthProvider", () => {
  it("logs in, sets token state and localStorage", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      new Response(JSON.stringify({ token: "demo-token-bnpl" }), { status: 200 })));

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    expect(screen.getByTestId("token")).toHaveTextContent("none");
    await userEvent.click(screen.getByRole("button", { name: "do-login" }));

    await waitFor(() =>
      expect(screen.getByTestId("token")).toHaveTextContent("demo-token-bnpl"));
    expect(localStorage.getItem("bnpl.token")).toBe("demo-token-bnpl");
  });
});
