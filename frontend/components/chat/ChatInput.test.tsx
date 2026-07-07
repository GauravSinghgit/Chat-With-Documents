import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ChatInput } from "./ChatInput";

vi.mock("@/lib/api/documents", () => ({
  documentsApi: { list: vi.fn().mockResolvedValue({ ok: true, data: { total: 0, documents: [] } }) },
}));

function setup(overrides: Partial<React.ComponentProps<typeof ChatInput>> = {}) {
  const onSend = vi.fn();
  const onCancel = vi.fn();
  const onDocSelect = vi.fn();
  render(
    <ChatInput
      onSend={onSend}
      isStreaming={false}
      onCancel={onCancel}
      focusDoc={null}
      onDocSelect={onDocSelect}
      {...overrides}
    />
  );
  return { onSend, onCancel, onDocSelect };
}

describe("ChatInput", () => {
  it("disables the send button until there is non-whitespace text", async () => {
    setup();
    const sendButton = screen.getByTitle("Send (Enter)");
    expect(sendButton).toBeDisabled();

    await userEvent.type(screen.getByPlaceholderText(/type a message/i), "   ");
    expect(sendButton).toBeDisabled();

    await userEvent.type(screen.getByPlaceholderText(/type a message/i), "hi");
    expect(sendButton).toBeEnabled();
  });

  it("sends the trimmed message and clears the input on submit", async () => {
    const { onSend } = setup();
    const textarea = screen.getByPlaceholderText(/type a message/i);

    await userEvent.type(textarea, "  hello world  ");
    await userEvent.click(screen.getByTitle("Send (Enter)"));

    expect(onSend).toHaveBeenCalledWith("hello world", {
      use_rag: true,
      use_tools: true,
      use_agent: false,
    });
    expect(textarea).toHaveValue("");
  });

  it("sends on Enter but inserts a newline on Shift+Enter", async () => {
    const { onSend } = setup();
    const textarea = screen.getByPlaceholderText(/type a message/i);

    await userEvent.type(textarea, "line one{Shift>}{Enter}{/Shift}line two");
    expect(onSend).not.toHaveBeenCalled();
    expect(textarea).toHaveValue("line one\nline two");

    await userEvent.type(textarea, "{Enter}");
    expect(onSend).toHaveBeenCalledTimes(1);
  });

  it("includes use_agent: true after toggling the Agent chip on", async () => {
    const { onSend } = setup();
    const textarea = screen.getByPlaceholderText(/type a message/i);

    await userEvent.click(screen.getByTitle("Enable ReAct agent loop"));
    await userEvent.type(textarea, "test");
    await userEvent.click(screen.getByTitle("Send (Enter)"));

    expect(onSend).toHaveBeenCalledWith(
      "test",
      expect.objectContaining({ use_agent: true })
    );
  });

  it("shows a stop button instead of send while streaming", () => {
    setup({ isStreaming: true });
    expect(screen.getByTitle("Stop generation")).toBeInTheDocument();
    expect(screen.queryByTitle("Send (Enter)")).not.toBeInTheDocument();
  });
});
