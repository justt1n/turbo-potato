import { describe, expect, it } from "vitest";
import { buildLinePath } from "./chart";

describe("buildLinePath", () => {
  it("returns an SVG path for multiple points", () => {
    const path = buildLinePath([10, 20, 15], 200, 100);
    expect(path.startsWith("M")).toBe(true);
    expect(path.includes("L")).toBe(true);
  });

  it("returns empty string for empty data", () => {
    expect(buildLinePath([], 200, 100)).toBe("");
  });
});

