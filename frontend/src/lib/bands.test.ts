// frontend/src/lib/bands.test.ts
import { describe, expect, it } from "vitest";
import { dtiBandClass, riskClass } from "./bands";

describe("bands", () => {
  it("maps DTI bands to color classes", () => {
    expect(dtiBandClass("SAFE")).toContain("green");
    expect(dtiBandClass("ACCEPTABLE")).toContain("blue");
    expect(dtiBandClass("WARNING")).toContain("amber");
    expect(dtiBandClass("DANGER")).toContain("red");
  });
  it("maps risk score to color classes by quartile", () => {
    expect(riskClass(10)).toContain("green");
    expect(riskClass(40)).toContain("blue");
    expect(riskClass(70)).toContain("amber");
    expect(riskClass(90)).toContain("red");
  });
});
