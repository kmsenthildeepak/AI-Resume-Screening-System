const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage();
  await page.goto('http://localhost:8501');
  await page.waitForTimeout(3000);

  // 1. Fill textarea
  const textarea = page.locator('textarea[aria-label="Job Description Text"]');
  await textarea.fill('My Test Job Description 123');
  await textarea.press('Tab');
  await page.waitForTimeout(2000);

  // 2. Upload a file
  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(path.resolve('sample_resumes/resume_01_strong_match.txt'));
  await page.waitForTimeout(2000);

  console.log('Filled textarea & uploaded file. Current textarea:', await textarea.inputValue());

  // 3. Navigate to Screening Overview
  console.log('Navigating to Screening Overview...');
  const overviewRadio = page.getByRole('radiogroup').getByText('Screening Overview');
  await overviewRadio.click();
  await page.waitForTimeout(2000);

  // 4. Navigate back to Candidates
  console.log('Navigating back to Candidates...');
  const candidatesRadio = page.getByRole('radiogroup').getByText('Candidates');
  await candidatesRadio.click();
  await page.waitForTimeout(2000);

  const valAfter = await textarea.inputValue();
  console.log('Textarea value after returning to Candidates: "' + valAfter + '"');

  const bodyText = await page.innerText('body');
  const hasQueueCard = bodyText.includes('candidate document(s) in active queue');
  console.log('Active Screening Queue displayed on Candidates page:', hasQueueCard);

  await browser.close();
})();
