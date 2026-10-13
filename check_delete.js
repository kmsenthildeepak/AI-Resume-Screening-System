const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage();
  await page.goto('http://localhost:8501');
  await page.waitForTimeout(2000);

  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(path.resolve('sample_resumes/resume_02_partial_match.docx'));
  await page.waitForTimeout(3000);

  console.log('Clicking delete button...');
  // Find delete button
  const deleteBtn = page.locator('[data-testid="stFileUploaderDeleteFile"], [aria-label*="Delete"], button[aria-label*="Remove"]').first();
  console.log('Delete button text/html:', await deleteBtn.innerHTML());
  await deleteBtn.click();
  await page.waitForTimeout(3000);

  const remainingFiles = await page.locator('[data-testid="stFileUploaderDeleteFile"]').count();
  console.log('Remaining delete buttons after click:', remainingFiles);
  await browser.close();
})();
