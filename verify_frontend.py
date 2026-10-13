import os
import asyncio
from playwright.async_api import async_playwright

async def verify_landing_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        print("Navigating to http://127.0.0.1:5173/...")
        await page.goto("http://127.0.0.1:5173/", wait_until="networkidle")

        # Verify page title
        title = await page.title()
        print(f"Page Title: {title}")
        assert "AI Resume Screening System" in title

        # Verify Header text
        header = await page.text_content("h1")
        print(f"Header: {header}")
        assert "AI-Powered Resume Screening System" in header

        # Verify CTA button presence and href
        cta = page.locator('a:has-text("Open Screening Dashboard")')
        cta_count = await cta.count()
        print(f"CTA Button count: {cta_count}")
        assert cta_count >= 1
        href = await cta.first.get_attribute("href")
        print(f"CTA href: {href}")
        assert href == "http://localhost:8501"

        # Verify cards are present
        cards = page.locator('div[class*="group/product"]')
        card_count = await cards.count()
        print(f"Rendered Cards count: {card_count}")
        assert card_count == 15

        # Test scroll behavior
        print("Testing scroll parallax...")
        await page.evaluate("window.scrollBy(0, 800)")
        await asyncio.sleep(0.5)

        # Take screenshot of Hero
        screenshot_path = "E:/AI_Resume_Screening_System/frontend_verification.png"
        await page.screenshot(path=screenshot_path, full_page=False)
        print(f"Saved screenshot to {screenshot_path}")

        # Check mobile responsiveness
        print("Checking mobile viewport...")
        await page.set_viewport_size({"width": 375, "height": 667})
        await asyncio.sleep(0.3)
        mobile_header = await page.text_content("h1")
        assert "AI-Powered Resume Screening System" in mobile_header
        print("Mobile verification successful!")

        await browser.close()
        print("All Hero Parallax verification checks PASSED successfully!")

if __name__ == "__main__":
    asyncio.run(verify_landing_page())
