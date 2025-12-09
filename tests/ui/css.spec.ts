import { describe, expect, it } from "vitest";

import { cn } from "@/utils/css";

describe("cn", () => {
  it("should concatenate classes", () => {
    expect(cn("A", "B")).toEqual("A B");
  });

  it("should handle empty and undefined values", () => {
    expect(cn("A", "", undefined, "B")).toEqual("A B");
  });
});
