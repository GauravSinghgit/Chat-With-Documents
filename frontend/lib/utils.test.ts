import { describe, expect, it } from "vitest";
import { cn, formatDate, truncate } from "./utils";

describe("cn", () => {
  it("merges class names and resolves tailwind conflicts", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
    expect(cn("text-sm", undefined, "font-bold")).toBe("text-sm font-bold");
  });
});

describe("truncate", () => {
  it("leaves short strings untouched", () => {
    expect(truncate("hello", 10)).toBe("hello");
  });

  it("truncates long strings and appends an ellipsis", () => {
    expect(truncate("hello world", 5)).toBe("hello…");
  });
});

describe("formatDate", () => {
  it("shows 'just now' for the current moment", () => {
    expect(formatDate(new Date())).toBe("just now");
  });

  it("shows minutes ago for recent timestamps", () => {
    const fiveMinAgo = new Date(Date.now() - 5 * 60000);
    expect(formatDate(fiveMinAgo)).toBe("5m ago");
  });

  it("shows hours ago for timestamps within a day", () => {
    const threeHoursAgo = new Date(Date.now() - 3 * 3600000);
    expect(formatDate(threeHoursAgo)).toBe("3h ago");
  });
});
