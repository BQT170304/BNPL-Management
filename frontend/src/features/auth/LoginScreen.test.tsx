import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../../state/auth";
import { LoginScreen } from "./LoginScreen";

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("LoginScreen", () => {
  it("posts credentials to /api/auth/login and stores the token", async () => {
    const spy = vi.fn(async () =>
      new Response(JSON.stringify({ token: "demo-token-bnpl" }), { status: 200 }));
    vi.stubGlobal("fetch", spy);

    render(
      <AuthProvider>
        <LoginScreen />
      </AuthProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: /đăng nhập/i }));

    await waitFor(() =>
      expect(localStorage.getItem("bnpl.token")).toBe("demo-token-bnpl"));

    expect(spy).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ username: "nguyenvana", password: "123456" }),
      }),
    );
  });

  it("shows an error banner on failure", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      new Response(JSON.stringify({ detail: "Sai thông tin đăng nhập" }), { status: 401 })));

    render(
      <AuthProvider>
        <LoginScreen />
      </AuthProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: /đăng nhập/i }));
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/sai thông tin/i));
  });
});
