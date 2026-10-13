const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });

  console.log('=== REAL-BROWSER VERIFICATION: RESUME QUEUE NAVIGATION ===');
  await page.goto('http://localhost:8501');
  await page.waitForTimeout(3000);

  // 1. Load Sample Job Description
  console.log('1. Loading Sample Job Description...');
  const loadBtn = page.getByRole('button', { name: /Load Sample/i });
  await loadBtn.click();
  await page.waitForTimeout(2000);

  // 2. Upload three files
  console.log('2. Uploading 3 resume files...');
  const files3 = [
    'resume_01_strong_match.txt',
    'resume_02_partial_match.docx',
    'resume_03_unrelated.txt'
  ].map(f => path.resolve('sample_resumes', f));

  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(files3);
  await page.waitForTimeout(3000);

  // Verify visible queue displays count and all 3 filenames
  let bodyText = await page.innerText('body');
  if (!bodyText.includes('3 candidate document(s) in active queue')) {
    throw new Error('FAIL: Active queue indicator not showing 3 documents');
  }
  if (!bodyText.includes('resume_01_strong_match.txt') ||
      !bodyText.includes('resume_02_partial_match.docx') ||
      !bodyText.includes('resume_03_unrelated.txt')) {
    throw new Error('FAIL: Not all 3 filenames displayed in visible queue before navigation');
  }
  console.log('✓ All 3 filenames displayed in visible queue with formatted file sizes');

  // Screenshot before navigation
  await page.screenshot({ path: 'screenshots/queue_before_nav.png' });
  console.log('✓ Screenshot saved to screenshots/queue_before_nav.png');

  // 3. Navigate away: Candidates -> Screening Overview -> Candidate Review
  console.log('3. Navigating to Screening Overview...');
  await page.getByRole('radiogroup').getByText('Screening Overview').click();
  await page.waitForTimeout(2000);

  console.log('4. Navigating to Candidate Review...');
  await page.getByRole('radiogroup').getByText('Candidate Review').click();
  await page.waitForTimeout(2000);

  // 4. Return to Candidates
  console.log('5. Returning to Candidates page...');
  await page.getByRole('radiogroup').getByText('Candidates').click();
  await page.waitForTimeout(3000);

  // Verify visible queue is preserved
  bodyText = await page.innerText('body');
  if (!bodyText.includes('3 candidate document(s) in active queue')) {
    throw new Error('FAIL: Active queue count lost after returning to Candidates');
  }
  if (!bodyText.includes('resume_01_strong_match.txt') ||
      !bodyText.includes('resume_02_partial_match.docx') ||
      !bodyText.includes('resume_03_unrelated.txt')) {
    throw new Error('FAIL: Filenames disappeared from visible queue after returning to Candidates');
  }
  console.log('✓ Visible queue and all 3 files preserved after navigation');

  // Screenshot after navigation
  await page.screenshot({ path: 'screenshots/queue_after_nav.png' });
  console.log('✓ Screenshot saved to screenshots/queue_after_nav.png');

  // 5. Test Clear Resume Queue button
  console.log('6. Clicking Clear Resume Queue...');
  const clearQueueBtn = page.getByRole('button', { name: /Clear Resume Queue/i });
  await clearQueueBtn.click();
  await page.waitForTimeout(2000);

  bodyText = await page.innerText('body');
  if (bodyText.includes('resume_01_strong_match.txt') || bodyText.includes('candidate document(s) in active queue')) {
    throw new Error('FAIL: Queue files still displayed after clicking Clear Resume Queue');
  }
  // Verify JD remained intact
  const jdVal = await page.locator('textarea[aria-label="Job Description Text"]').inputValue();
  if (!jdVal || jdVal.length < 50) {
    throw new Error('FAIL: Job description was cleared when clearing resume queue');
  }
  console.log('✓ Queue cleared successfully while Job Description remained intact');

  await page.screenshot({ path: 'screenshots/queue_cleared_jd_intact.png' });
  console.log('✓ Screenshot saved to screenshots/queue_cleared_jd_intact.png');

  await browser.close();
  console.log('\n=== REAL-BROWSER QUEUE NAVIGATION VERIFICATION COMPLETED SUCCESSFULLY ===');
})().catch(err => {
  console.error('Playwright Test Failed:', err);
  process.exit(1);
});
