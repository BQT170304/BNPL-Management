// frontend/src/App.test.tsx
import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { App } from "./App";

beforeEach(() => localStorage.clear());
afterEach(() => localStorage.clear());

describe("App", () => {
  it("shows the login screen when there is no token", () => {
    render(<App />);
    expect(screen.getByRole("button", { name: /đăng nhập/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /nhập CIF/i })).not.toBeInTheDocument();
  });

  it("renders the authenticated nav including the forecast tab when a token is present", () => {
    localStorage.setItem("bnpl.token", "demo-token-bnpl");
    render(<App />);
    expect(screen.getByRole("button", { name: /nhập CIF/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /hồ sơ/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /phân tích/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /đánh giá/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /dự báo/i })).toBeInTheDocument();
  });

  it("shows a hint when no active profile for analysis", async () => {
    localStorage.setItem("bnpl.token", "demo-token-bnpl");
    render(<App />);
    // default section is Import; switching to Analysis without a profile shows hint
    screen.getByRole("button", { name: /phân tích/i }).click();
    expect(await screen.findByText(/chưa có hồ sơ/i)).toBeInTheDocument();
  });
});
