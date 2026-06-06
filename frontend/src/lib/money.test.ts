// frontend/src/lib/money.test.ts
import { describe, expect, it } from "vitest";
import { formatVnd, parseVnd } from "./money";

describe("money", () => {
  it("formats with dot separators and ₫", () => {
    expect(formatVnd(14_500_000)).toBe("14.500.000 ₫");
    expect(formatVnd(0)).toBe("0 ₫");
    expect(formatVnd(-800_000)).toBe("-800.000 ₫");
  });
  it("parses digit strings (ignoring separators) to int", () => {
    expect(parseVnd("14.500.000")).toBe(14_500_000);
    expect(parseVnd("14,500,000 ₫")).toBe(14_500_000);
    expect(parseVnd("")).toBe(0);
    expect(parseVnd("abc")).toBe(0);
  });
});
