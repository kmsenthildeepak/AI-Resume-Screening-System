import { chromium } from "playwright";

async function verify() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  console.log("Navigating to http://127.0.0.1:5173/...");
  await page.goto("http://127.0.0.1:5173/", { waitUntil: "networkidle" });

  const title = await page.title();
  console.log(`Page Title: ${title}`);
  if (!title.includes("AI Resume Screening System")) throw new Error("Title mismatch");

  const header = await page.textContent("h1");
  console.log(`Header: ${header?.trim()}`);
  if (!header?.includes("AI-Powered Resume Screening System")) throw new Error("Header mismatch");

  const cta = page.locator('a:has-text("Open Screening Dashboard")');
  const ctaCount = await cta.count();
  console.log(`CTA Count: ${ctaCount}`);
  if (ctaCount < 1) throw new Error("CTA not found");

  const href = await cta.first().getAttribute("href");
  console.log(`CTA Link: ${href}`);
  if (href !== "http://localhost:8501") throw new Error("CTA href mismatch");

  const cards = page.locator('div[class*="group/product"]');
  const cardCount = await cards.count();
  console.log(`Card Count: ${cardCount}`);
  if (cardCount !== 15) throw new Error(`Expected 15 cards, got ${cardCount}`);

  console.log("Testing scroll interaction...");
  await page.evaluate(() => window.scrollBy(0, 600));
  await page.waitForTimeout(500);

  const screenshotPath = "E:/AI_Resume_Screening_System/frontend_verified.png";
  await page.screenshot({ path: screenshotPath });
  console.log(`Screenshot saved to: ${screenshotPath}`);

  // Test mobile
  await page.setViewportSize({ width: 375, height: 667 });
  await page.waitForTimeout(300);
  const mobileHeader = await page.textContent("h1");
  console.log(`Mobile Header: ${mobileHeader?.trim()}`);

  await browser.close();
  console.log("VERIFICATION COMPLETE: ALL CHECKS PASSED!");
}

verify().catch((err) => {
  console.error(err);
  process.exit(1);
});
