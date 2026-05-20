import { chromium, expect } from "@playwright/test";

const baseUrl = process.env.LAB_DASHBOARD_URL ?? "http://127.0.0.1:3000";
const headless = process.env.LAB_DASHBOARD_HEADLESS !== "0";
const viewports = [
  { name: "desktop", width: 1440, height: 1000 },
  { name: "mobile", width: 390, height: 844 }
];

const browser = await chromium.launch({ headless });

try {
  for (const viewport of viewports) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height }
    });
    const page = await context.newPage();
    const browserIssues = [];

    page.on("console", (message) => {
      if (["error", "warning"].includes(message.type())) {
        browserIssues.push(`${message.type()}: ${message.text()}`);
      }
    });
    page.on("pageerror", (error) => {
      browserIssues.push(`pageerror: ${error.message}`);
    });

    await page.goto(baseUrl, { waitUntil: "networkidle" });
    await expect(page.getByText("AI Reliability Platform")).toBeVisible();

    await page.getByRole("button", { name: /Ingest Corpus/i }).click();
    await expect(page.locator(".mini-stats dd").nth(0)).toHaveText("4", { timeout: 15_000 });
    await expect(page.locator(".mini-stats dd").nth(1)).toHaveText("12", { timeout: 15_000 });

    await page.getByRole("button", { name: /Run Query/i }).click();
    await expect(page.getByText("model-release.md").first()).toBeVisible();

    await page.getByRole("button", { name: /Run Eval/i }).click();
    await expect(page.getByText("4/4").first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("sensitive-request-refusal")).toBeVisible();

    const overflow = await page.evaluate(() =>
      Array.from(document.querySelectorAll("*"))
        .filter((element) => element.scrollWidth > element.clientWidth + 1)
        .map((element) => ({
          tag: element.tagName,
          className:
            typeof element.className === "string" ? element.className : String(element.className),
          text: element.textContent?.trim().slice(0, 80) ?? "",
          scrollWidth: element.scrollWidth,
          clientWidth: element.clientWidth
        }))
    );

    if (overflow.length > 0) {
      throw new Error(
        `${viewport.name} viewport has horizontal overflow: ${JSON.stringify(overflow.slice(0, 5))}`
      );
    }
    if (browserIssues.length > 0) {
      throw new Error(`${viewport.name} viewport browser issues: ${browserIssues.join("; ")}`);
    }

    await context.close();
    console.log(`${viewport.name} dashboard QA passed`);
  }
} finally {
  await browser.close();
}
