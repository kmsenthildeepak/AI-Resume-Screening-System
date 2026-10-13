const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage();
  await page.goto('http://localhost:8501');
  await page.waitForTimeout(2000);

  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(path.resolve('sample_resumes/resume_02_partial_match.docx'));
  await page.waitForTimeout(2000);
  
  const deleteBtns = await page.locator('[data-testid="stFileUploaderDeleteFile"], [aria-label*="Remove"], button[kind="fileUploaderDelete"]').count();
  console.log('Delete button count:', deleteBtns);

  const fileNames = await page.locator('[data-testid="stFileUploaderFileData"]').allInnerTexts();
  console.log('Files currently in uploader:', fileNames);

  await browser.close();
})();
