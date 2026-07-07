import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MessageBubble } from "./MessageBubble";
import type { Message } from "@/lib/api/types";

function makeMessage(overrides: Partial<Message> = {}): Message {
  return {
    id: 1,
    role: "assistant",
    content: "Hello there",
    timestamp: new Date().toISOString(),
    ...overrides,
  };
}

describe("MessageBubble", () => {
  it("renders message content", () => {
    render(<MessageBubble message={makeMessage({ content: "Hi from the assistant" })} />);
    expect(screen.getByText("Hi from the assistant")).toBeInTheDocument();
  });

  it("escapes HTML in message content instead of rendering it", () => {
    render(<MessageBubble message={makeMessage({ content: "<script>alert(1)</script>" })} />);
    expect(document.querySelector("script")).not.toBeInTheDocument();
    expect(screen.getByText("<script>alert(1)</script>")).toBeInTheDocument();
  });

  it("renders bold markdown as strong text", () => {
    render(<MessageBubble message={makeMessage({ content: "**bold text**" })} />);
    const strong = document.querySelector("strong");
    expect(strong).toHaveTextContent("bold text");
  });

  it("shows a typing indicator while streaming with no content yet", () => {
    const { container } = render(
      <MessageBubble message={makeMessage({ content: "" })} isStreaming />
    );
    expect(container.querySelectorAll(".animate-bounce")).toHaveLength(3);
  });
});
