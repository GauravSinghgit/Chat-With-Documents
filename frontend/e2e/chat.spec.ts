import { test, expect } from "@playwright/test";

test.describe("core flow: register -> chat -> logout", () => {
  test("a new user can register, chat, and log out", async ({ page }) => {
    const email = `e2e-${Date.now()}@example.com`;
    const password = "TestPass123!";

    await page.goto("/register");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Create account" }).click();

    await expect(page).toHaveURL(/\/chat/);

    await page.goto(`/chat/e2e-conv-${Date.now()}`);
    const input = page.getByPlaceholder(/type a message/i);
    await input.fill("Hello, this is an end-to-end test.");
    await page.getByTitle("Send (Enter)").click();

    await expect(page.getByText("Hello, this is an end-to-end test.")).toBeVisible();
    await expect(page.locator(".message-content").last()).not.toBeEmpty({ timeout: 20000 });

    await page.getByRole("button", { name: /sign out/i }).click();
    await expect(page).toHaveURL(/\/login/);

    // Protected route should now server-side redirect back to /login.
    await page.goto("/chat");
    await expect(page).toHaveURL(/\/login/);
  });
});
