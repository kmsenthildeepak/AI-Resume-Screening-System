import assert from "node:assert";

// Test extraction logic with real payload shape from the 4 resumes
function extractSkillSnippets(evidence) {
  if (!evidence) return [];
  if (Array.isArray(evidence)) {
    return evidence.filter((s) => typeof s === "string");
  }
  if (typeof evidence === "object" && evidence !== null) {
    if (Array.isArray(evidence.snippets)) {
      return evidence.snippets.filter((s) => typeof s === "string");
    }
    if (Array.isArray(evidence.records)) {
      return evidence.records
        .map((r) => r?.snippet)
        .filter((s) => typeof s === "string");
    }
  }
  return [];
}

function extractSkillTier(evidence) {
  if (evidence && typeof evidence === "object" && !Array.isArray(evidence)) {
    return typeof evidence.tier === "string" ? evidence.tier : null;
  }
  return null;
}

console.log("Testing extractSkillSnippets and extractSkillTier...");

// Case 1: Backend dict shape with snippets list and tier (The exact bug cause)
const backendEvidence = {
  tier: "work_experience",
  is_demonstrated: true,
  snippets: [
    "- Developed client-facing web dashboards using React and Django REST framework.",
    "- Integrated MySQL relational database models and wrote REST APIs."
  ],
  records: [
    { section: "experience", category: "work_experience", snippet: "- Developed client-facing web dashboards." }
  ]
};

const snips1 = extractSkillSnippets(backendEvidence);
assert.strictEqual(snips1.length, 2, "Expected 2 snippets extracted from backend dict");
assert.strictEqual(extractSkillTier(backendEvidence), "work_experience");

// Case 2: Plain array (fallback/legacy)
const arrayEvidence = ["Quote 1", "Quote 2"];
const snips2 = extractSkillSnippets(arrayEvidence);
assert.strictEqual(snips2.length, 2);
assert.strictEqual(extractSkillTier(arrayEvidence), null);

// Case 3: Empty object or bare mention without snippets
const emptyEvidence = {};
assert.strictEqual(extractSkillSnippets(emptyEvidence).length, 0);
assert.strictEqual(extractSkillTier(emptyEvidence), null);

// Case 4: Null or undefined
assert.strictEqual(extractSkillSnippets(null).length, 0);
assert.strictEqual(extractSkillSnippets(undefined).length, 0);
assert.strictEqual(extractSkillTier(null), null);
assert.strictEqual(extractSkillTier(undefined), null);

console.log("✓ All skill evidence helper tests passed!");
