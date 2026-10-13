import { chromium } from "playwright";
import fs from "fs";
import path from "path";

async function renderPng() {
  const svgPath = path.resolve("../assets/logo.svg");
  const svgContent = fs.readFileSync(svgPath, "utf-8");

  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  });

  const page = await browser.newPage({ viewport: { width: 512, height: 512 } });

  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          body, html { margin: 0; padding: 0; background: transparent; overflow: hidden; width: 512px; height: 512px; }
          svg { width: 512px; height: 512px; display: block; }
        </style>
      </head>
      <body>
        ${svgContent}
      </body>
    </html>
  `;

  await page.setContent(html);
  await page.waitForTimeout(300);

  const pngPath = path.resolve("assets/logo.png");
  await page.screenshot({ path: pngPath, omitBackground: true });
  console.log("Rendered logo.png successfully at:", pngPath);

  // Also render 64x64 favicon.png
  await page.setViewportSize({ width: 64, height: 64 });
  const smallHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          body, html { margin: 0; padding: 0; background: transparent; overflow: hidden; width: 64px; height: 64px; }
          svg { width: 64px; height: 64px; display: block; }
        </style>
      </head>
      <body>
        ${svgContent}
      </body>
    </html>
  `;
  await page.setContent(smallHtml);
  await page.waitForTimeout(200);
  const faviconPngPath = path.resolve("assets/favicon.png");
  await page.screenshot({ path: faviconPngPath, omitBackground: true });
  console.log("Rendered favicon.png successfully at:", faviconPngPath);

  await browser.close();
}

renderPng().catch((e) => {
  console.error("Error generating PNG logo:", e);
  process.exit(1);
});
