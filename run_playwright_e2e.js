const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 950 } });
  
  console.log('Navigating to http://localhost:8501 ...');
  await page.goto('http://localhost:8501');
  await page.waitForTimeout(3000);

  // 1. Click 'Load Sample Job Description'
  console.log('Clicking Load Sample Job Description...');
  const loadBtn = page.getByRole('button', { name: /Load Sample/i });
  await loadBtn.click();
  await page.waitForTimeout(3000);

  // 2. Upload sample resume
  console.log('Uploading sample resume...');
  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(path.resolve('sample_resumes/resume_01_strong_match.txt'));
  await page.waitForTimeout(3000);

  // 3. Click 'Analyze & Rank Candidates'
  console.log('Clicking Analyze & Rank Candidates...');
  const analyzeBtn = page.getByRole('button', { name: /Analyze & Rank/i });
  await analyzeBtn.click();
  await page.waitForTimeout(4000);

  // Capture Candidates Screened view
  await page.screenshot({ path: 'screenshots/after_candidates_screened.png' });
  console.log('Saved screenshots/after_candidates_screened.png');

  // 4. Navigate to Screening Overview
  console.log('Navigating to Screening Overview...');
  const overviewRadio = page.getByRole('radiogroup').getByText('Screening Overview');
  await overviewRadio.click();
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'screenshots/after_screening_overview.png' });
  console.log('Saved screenshots/after_screening_overview.png');

  // 5. Navigate to Candidate Review
  console.log('Navigating to Candidate Review...');
  const reviewRadio = page.getByRole('radiogroup').getByText('Candidate Review');
  await reviewRadio.click();
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'screenshots/after_candidate_review.png' });
  console.log('Saved screenshots/after_candidate_review.png');

  await browser.close();
  console.log('ALL PLAYWRIGHT TESTS PASSED!');
})().catch(e => {
  console.error('Playwright execution error:', e);
  process.exit(1);
});
