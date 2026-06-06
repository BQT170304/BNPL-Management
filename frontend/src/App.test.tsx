// frontend/src/App.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("renders the nav with four sections", () => {
    render(<App />);
    expect(screen.getByRole("button", { name: /nhập CIF/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /hồ sơ/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /phân tích/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /đánh giá/i })).toBeInTheDocument();
  });

  it("shows a hint when no active profile for analysis", async () => {
    localStorage.clear();
    render(<App />);
    // default section is Import; switching to Analysis without a profile shows hint
    screen.getByRole("button", { name: /phân tích/i }).click();
    expect(await screen.findByText(/chưa có hồ sơ/i)).toBeInTheDocument();
  });
});
