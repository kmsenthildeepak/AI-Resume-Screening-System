const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });

  console.log('--- STARTING PLAYWRIGHT SCENARIOS A-E ---');

  // ==========================================
  // SCENARIO A: Empty State & Load Sample JD
  // ==========================================
  console.log('\n[Scenario A] Opening new session for empty state check...');
  const pageA = await browser.newPage({ viewport: { width: 1280, height: 950 } });
  await pageA.goto('http://localhost:8501');
  await pageA.waitForTimeout(3000);

  const loadBtnA = pageA.getByRole('button', { name: /Load Sample/i });
  await loadBtnA.click();
  await pageA.waitForTimeout(3000);

  // Verify dynamic job title
  const headerTextA = await pageA.innerText('.ats-top-header');
  if (!headerTextA.includes('Job: Java Full Stack Developer')) {
    throw new Error('Scenario A Failed: Expected "Job: Java Full Stack Developer" in top header');
  }
  // Verify no candidates are auto-injected
  const bodyTextA = await pageA.innerText('body');
  if (bodyTextA.includes('Alex Morgan') || bodyTextA.includes('Jordan Lee')) {
    throw new Error('Scenario A Failed: Prebuilt sample candidates were auto-injected before screening!');
  }
  if (!bodyTextA.includes('No candidates currently screened')) {
    throw new Error('Scenario A Failed: Empty state banner was not displayed.');
  }
  console.log('✓ Scenario A Passed: Loading JD updates title without injecting sample candidates.');
  await pageA.close();

  // ==========================================
  // SCENARIO B: One Uploaded Resume
  // ==========================================
  console.log('\n[Scenario B] Opening session with single resume upload (resume_02_partial_match.docx)...');
  const pageB = await browser.newPage({ viewport: { width: 1280, height: 950 } });
  await pageB.goto('http://localhost:8501');
  await pageB.waitForTimeout(3000);

  const loadBtnB = pageB.getByRole('button', { name: /Load Sample/i });
  await loadBtnB.click();
  await pageB.waitForTimeout(2000);

  const fileInputB = pageB.locator('input[type="file"]').first();
  await fileInputB.setInputFiles(path.resolve('sample_resumes/resume_02_partial_match.docx'));
  await pageB.waitForTimeout(3000);

  const analyzeBtnB = pageB.getByRole('button', { name: /Analyze & Rank/i });
  await analyzeBtnB.click();
  await pageB.waitForTimeout(4000);

  const tableTextB = await pageB.innerText('.leaderboard-table');
  if (!tableTextB.includes('Jordan Lee') || !tableTextB.includes('resume_02_partial_match.docx')) {
    throw new Error('Scenario B Failed: Jordan Lee not found in table.');
  }
  if (tableTextB.includes('Alex Morgan') || tableTextB.includes('Taylor Smith')) {
    throw new Error('Scenario B Failed: Other sample candidates found in table!');
  }
  console.log('✓ Scenario B Passed: Uploaded single resume screens strictly that candidate.');
  await pageB.close();

  // ==========================================
  // SCENARIO C: Multiple Uploaded Resumes
  // ==========================================
  console.log('\n[Scenario C] Opening session with multiple resumes (resume_01 and resume_03)...');
  const pageC = await browser.newPage({ viewport: { width: 1280, height: 950 } });
  await pageC.goto('http://localhost:8501');
  await pageC.waitForTimeout(3000);

  const loadBtnC = pageC.getByRole('button', { name: /Load Sample/i });
  await loadBtnC.click();
  await pageC.waitForTimeout(2000);

  const fileInputC = pageC.locator('input[type="file"]').first();
  await fileInputC.setInputFiles([
    path.resolve('sample_resumes/resume_01_strong_match.txt'),
    path.resolve('sample_resumes/resume_03_unrelated.txt')
  ]);
  await pageC.waitForTimeout(3000);

  const analyzeBtnC = pageC.getByRole('button', { name: /Analyze & Rank/i });
  await analyzeBtnC.click();
  await pageC.waitForTimeout(4000);

  const tableTextC = await pageC.innerText('.leaderboard-table');
  if (!tableTextC.includes('Alex Morgan') || !tableTextC.includes('Taylor Smith')) {
    throw new Error('Scenario C Failed: Expected Alex Morgan and Taylor Smith.');
  }
  if (tableTextC.includes('Jordan Lee')) {
    throw new Error('Scenario C Failed: Jordan Lee from prior run was not cleared!');
  }
  console.log('✓ Scenario C Passed: Multiple uploaded resumes rank only those candidates.');

  // ==========================================
  // SCENARIO D: Stale Results Detection
  // ==========================================
  console.log('\n[Scenario D] Modifying JD text area to trigger stale warning...');
  const jdTextareaC = pageC.locator('textarea[aria-label="Job Description Text"]');
  await jdTextareaC.fill('Role: Python Full Stack Developer\nRequirements: Python, Django, PostgreSQL, Docker.');
  await jdTextareaC.press('Tab');
  await pageC.waitForTimeout(4000);

  const staleBody = await pageC.innerText('body');
  if (!staleBody.includes('modified since the last screening run')) {
    throw new Error('Scenario D Failed: Stale JD warning was not rendered.');
  }
  console.log('✓ Scenario D Passed: Stale warning appears when JD text changes.');

  // ==========================================
  // SCENARIO E: Navigation, Overview, and Review
  // ==========================================
  console.log('\n[Scenario E] Testing navigation & candidate review...');
  const reviewRadio = pageC.getByRole('radiogroup').getByText('Candidate Review');
  await reviewRadio.click();
  await pageC.waitForTimeout(3000);
  const reviewText = await pageC.innerText('body');
  if (!reviewText.includes('Alex Morgan') || !reviewText.includes('Evidence Quotes')) {
    throw new Error('Scenario E Failed: Candidate Review workspace did not render correctly.');
  }
  console.log('✓ Scenario E Passed: Navigation and split-panel dossier rendered cleanly.');

  // Take fresh verification screenshot
  await pageC.screenshot({ path: 'screenshots/playwright_verification_all_scenarios.png' });
  console.log('Saved screenshots/playwright_verification_all_scenarios.png');

  await pageC.close();
  await browser.close();
  console.log('\nALL 5 SCENARIOS (A, B, C, D, E) PASSED AND VERIFIED VIA PLAYWRIGHT!');
})().catch(e => {
  console.error('Playwright Error:', e);
  process.exit(1);
});
