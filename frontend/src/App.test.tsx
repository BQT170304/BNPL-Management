import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { App } from "./App";

beforeEach(() => localStorage.clear());
afterEach(() => localStorage.clear());

describe("App", () => {
  it("shows the login screen when there is no token", () => {
    render(<App />);
    expect(screen.getByRole("button", { name: /đăng nhập/i })).toBeInTheDocument();
  });

  it("renders the setup wizard when authenticated but no profile", () => {
    localStorage.setItem("bnpl.token", "demo-token-bnpl");
    render(<App />);
    expect(screen.getByText(/dữ liệu ngân hàng/i)).toBeInTheDocument();
    expect(screen.getByText(/hồ sơ tài chính/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /đăng xuất/i })).toBeInTheDocument();
  });

  it("shows the CIF import step by default in setup wizard", () => {
    localStorage.setItem("bnpl.token", "demo-token-bnpl");
    render(<App />);
    expect(screen.getByText(/dùng dữ liệu này/i)).toBeInTheDocument();
  });
});
