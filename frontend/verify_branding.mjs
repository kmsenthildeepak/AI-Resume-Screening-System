import { chromium } from "playwright";

async function verifyBranding() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  });

  console.log("=== 1. VERIFYING REACT FRONTEND BRANDING ===");
  const reactPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await reactPage.goto("http://127.0.0.1:5173/", { waitUntil: "networkidle" });

  const reactTitle = await reactPage.title();
  console.log(`React Page Title: "${reactTitle}"`);
  if (reactTitle !== "AI Resume Screening System") {
    throw new Error(`React title expected "AI Resume Screening System", got "${reactTitle}"`);
  }

  // Favicon check
  const faviconSvg = await reactPage.locator('link[rel="icon"]').getAttribute("href");
  console.log(`React Favicon href: ${faviconSvg}`);
  if (faviconSvg !== "/favicon.svg") throw new Error("React favicon href mismatch");

  // Logo check in navbar
  const navbarLogo = await reactPage.locator('header img[alt="AI Resume Screening System Logo"]');
  const logoVisible = await navbarLogo.isVisible();
  console.log(`Navbar Logo visible: ${logoVisible}`);
  if (!logoVisible) throw new Error("Navbar logo is not visible");

  // CTA button check
  const cta = reactPage.locator('a:has-text("Open Screening Dashboard")');
  const ctaHref = await cta.first().getAttribute("href");
  console.log(`React CTA link href: ${ctaHref}`);
  if (ctaHref !== "http://localhost:8501/?page=Candidates") throw new Error("React CTA link mismatch");

  await reactPage.screenshot({ path: "E:/AI_Resume_Screening_System/react_branding_verified.png" });
  console.log("React screenshot captured: react_branding_verified.png");

  console.log("\n=== 2. VERIFYING STREAMLIT APPLICATION BRANDING ===");
  const stPage = await browser.newPage({ viewport: { width: 1366, height: 850 } });
  await stPage.goto("http://127.0.0.1:8501/", { waitUntil: "networkidle" });
  await stPage.waitForTimeout(2000); // Allow Streamlit components to mount

  const stTitle = await stPage.title();
  console.log(`Streamlit Tab Title: "${stTitle}"`);
  if (stTitle !== "AI Resume Screening System") {
    throw new Error(`Streamlit title expected "AI Resume Screening System", got "${stTitle}"`);
  }

  // Sidebar brand check
  const sidebarBrandTitle = await stPage.locator('.sidebar-brand-title').textContent();
  console.log(`Streamlit Sidebar Brand Title: "${sidebarBrandTitle?.trim()}"`);
  if (!sidebarBrandTitle?.includes("AI Resume Screening System")) {
    throw new Error(`Sidebar brand title mismatch: "${sidebarBrandTitle}"`);
  }

  const sidebarIcon = await stPage.locator('img.sidebar-brand-icon');
  const sidebarIconCount = await sidebarIcon.count();
  console.log(`Streamlit Sidebar Brand Icon count: ${sidebarIconCount}`);
  if (sidebarIconCount === 0) {
    throw new Error("Sidebar brand logo icon not found");
  }

  // Check interactive functionality in Streamlit: Load Sample JD
  console.log("Testing Streamlit Load Sample Job Description...");
  const loadJdButton = stPage.locator('button:has-text("Load Sample Job Description")');
  await loadJdButton.click();
  await stPage.waitForTimeout(1500);

  const jdValue = await stPage.locator('textarea').inputValue();
  console.log(`JD Loaded Length: ${jdValue.length} characters`);
  if (!jdValue.includes("Java Full Stack Developer")) {
    throw new Error("Load sample JD failed");
  }

  await stPage.screenshot({ path: "E:/AI_Resume_Screening_System/streamlit_branding_verified.png" });
  console.log("Streamlit screenshot captured: streamlit_branding_verified.png");

  await browser.close();
  console.log("\n>>> ALL BRANDING VERIFICATIONS SUCCEEDED! <<<");
}

verifyBranding().catch((err) => {
  console.error("Verification failed:", err);
  process.exit(1);
});
