import { describe, expect, it } from "vitest";
import { formatCurrency } from "./formatCurrency";

describe("formatCurrency", () => {
  it("formats VND without decimals", () => {
    expect(formatCurrency(268000)).toContain("268.000");
  });
});
