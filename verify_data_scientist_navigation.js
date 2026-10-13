const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });

  console.log('=== DATA SCIENTIST 8-CANDIDATE NAVIGATION TEST ===');
  await page.goto('http://localhost:8501');
  await page.waitForTimeout(3000);

  // 1. Enter Data Scientist Job Description
  const dsJD = `Role: Data Scientist
Required Skills: Python, Machine Learning, Deep Learning, SQL, Pandas, NumPy, Scikit-Learn, TensorFlow, Statistics, NLP.
Experience: 3+ years building data science workflows, statistical modeling, and machine learning pipelines.`;

  console.log('1. Populating Data Scientist Job Description...');
  const jdTextarea = page.locator('textarea[aria-label="Job Description Text"]');
  await jdTextarea.fill(dsJD);
  await jdTextarea.press('Tab');
  await page.waitForTimeout(2000);

  // Verify Header Job Title updates to Data Scientist
  const headerText1 = await page.innerText('.ats-top-header');
  console.log('Header text:', headerText1.replace(/\s+/g, ' '));
  if (!headerText1.includes('Job: Data Scientist')) {
    throw new Error('Expected "Job: Data Scientist" in top header');
  }

  // 2. Upload all 8 resumes
  console.log('2. Uploading 8 candidate resumes...');
  const testFiles = [
    'candidate_01_lead_ds.txt',
    'candidate_02_ml_eng.txt',
    'candidate_03_nlp_scientist.txt',
    'candidate_04_data_analyst.txt',
    'candidate_05_python_dev.txt',
    'candidate_06_bi_analyst.txt',
    'candidate_07_junior_ds.txt',
    'candidate_08_sales.txt'
  ].map(f => path.resolve('sample_resumes/data_scientist_test', f));

  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(testFiles);
  await page.waitForTimeout(3000);

  // Check upload queue indicator
  const queueStatus = await page.innerText('body');
  if (!queueStatus.includes('8') || !queueStatus.includes('candidate document(s) in active queue')) {
    throw new Error('Upload queue did not reflect 8 queued documents');
  }
  console.log('✓ 8 candidate documents queued in active queue');

  // 3. Click Analyze & Rank Candidates
  console.log('3. Running screening analysis...');
  const analyzeBtn = page.getByRole('button', { name: /Analyze & Rank/i });
  await analyzeBtn.click();
  await page.waitForTimeout(5000);

  // Verify 8 candidates in leaderboard
  const rows = await page.locator('.leaderboard-table tbody tr').count();
  console.log(`Leaderboard rendered with ${rows} candidate rows.`);
  if (rows !== 8) {
    throw new Error(`Expected 8 candidates in table, got ${rows}`);
  }

  // 4. Navigate to Screening Overview
  console.log('4. Navigating to Screening Overview...');
  await page.getByRole('radiogroup').getByText('Screening Overview').click();
  await page.waitForTimeout(3000);

  const overviewBody = await page.innerText('body');
  if (!overviewBody.includes('Top Candidate Match') || !overviewBody.includes('Required Competency Coverage')) {
    throw new Error('Screening Overview did not display analytical metrics');
  }
  const overviewHeader = await page.innerText('.ats-top-header');
  if (!overviewHeader.includes('Job: Data Scientist')) {
    throw new Error('Screening Overview lost dynamic job title');
  }
  console.log('✓ Screening Overview displayed metrics for Job: Data Scientist');

  // 5. Navigate to Candidate Review
  console.log('5. Navigating to Candidate Review...');
  await page.getByRole('radiogroup').getByText('Candidate Review').click();
  await page.waitForTimeout(3000);

  const reviewBody = await page.innerText('body');
  if (!reviewBody.includes('Candidate Queue') || !reviewBody.includes('Alice Walker')) {
    throw new Error('Candidate Review did not display top candidate dossier');
  }
  console.log('✓ Candidate Review displayed candidate dossier');

  // 6. Navigate back to Candidates
  console.log('6. Navigating back to Candidates page...');
  await page.getByRole('radiogroup').getByText('Candidates').click();
  await page.waitForTimeout(3000);

  // VERIFY:
  // a) JD Textarea is NOT empty and contains original text
  const jdValAfter = await jdTextarea.inputValue();
  console.log('JD Textarea value length after return:', jdValAfter.length);
  if (!jdValAfter.includes('Role: Data Scientist') || !jdValAfter.includes('TensorFlow')) {
    throw new Error('FAIL: Job Description textarea was cleared after navigation!');
  }
  console.log('✓ Job Description persisted seamlessly across navigation');

  // b) Active Screening Queue card is visible with 8 documents
  const candBodyAfter = await page.innerText('body');
  if (!candBodyAfter.includes('8') || !candBodyAfter.includes('candidate document(s) in active queue')) {
    throw new Error('FAIL: Active screening queue was lost after navigation!');
  }
  console.log('✓ Active Screening Queue persisted with all 8 files across navigation');

  // c) Candidate table still shows 8 ranked candidates
  const rowsAfter = await page.locator('.leaderboard-table tbody tr').count();
  if (rowsAfter !== 8) {
    throw new Error(`FAIL: Leaderboard rows count changed to ${rowsAfter}`);
  }
  console.log('✓ Leaderboard table retained all 8 ranked candidates');

  // d) Header title is still Job: Data Scientist
  const headerAfter = await page.innerText('.ats-top-header');
  if (!headerAfter.includes('Job: Data Scientist')) {
    throw new Error('FAIL: Header lost Job: Data Scientist title');
  }
  console.log('✓ Header retained Job: Data Scientist');

  // Save verification screenshot
  await page.screenshot({ path: 'screenshots/playwright_data_scientist_nav_verified.png' });
  console.log('✓ Screenshot saved to screenshots/playwright_data_scientist_nav_verified.png');

  await browser.close();
  console.log('\n=== ALL DATA SCIENTIST NAVIGATION CHECKS PASSED PERFECTLY! ===');
})().catch(err => {
  console.error('Test Failed:', err);
  process.exit(1);
});
