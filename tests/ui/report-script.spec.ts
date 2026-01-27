/**
 * Tests for report generation script functions.
 * Uses jsdom environment to test DOM manipulation functions.
 * @vitest-environment jsdom
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Type definitions matching script.js JSDoc types
interface AxiomItem {
  id: string;
  description: string;
}

interface RealityItem {
  id: string;
  description: string;
}

interface EvaluationData {
  evaluation_outputs: unknown[];
  axiom_definitions?: AxiomItem[];
  reality_definitions?: RealityItem[];
}

// Mock window.evaluationData
declare global {
  interface Window {
    evaluationData: EvaluationData;
  }
}

/**
 * Escapes HTML special characters to prevent XSS attacks.
 * This is a copy of the function from script.js for testing.
 */
function escapeHtml(text: string | null | undefined): string {
  if (text == null) {
    return "";
  }
  const entityMap: Record<string, string> = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
    "/": "&#x2F;",
    "`": "&#x60;",
    "=": "&#x3D;"
  };
  return String(text).replace(/[&<>"'`=/]/g, (ch) => entityMap[ch]);
}

/**
 * Renders the axiom definitions section.
 * This is a copy of the function from script.js for testing.
 */
function renderAxiomDefinitions(): void {
  const container = document.getElementById("axiom-definitions-list");
  if (!container) {
    console.error("Error: axiom-definitions-list element not found");
    return;
  }

  const definitions = window.evaluationData.axiom_definitions;
  if (!definitions || definitions.length === 0) {
    container.innerHTML = '<p class="no-definitions">No axiom definitions available.</p>';
    return;
  }

  const definitionsHtml = definitions
    .map(
      (item: AxiomItem) => `
            <div class="definition-item">
                <span class="definition-id">${escapeHtml(item.id)}</span>
                <span class="definition-text">${escapeHtml(item.description)}</span>
            </div>
        `
    )
    .join("");

  container.innerHTML = definitionsHtml;
}

/**
 * Renders the reality item definitions section.
 * This is a copy of the function from script.js for testing.
 */
function renderRealityDefinitions(): void {
  const container = document.getElementById("reality-definitions-list");
  if (!container) {
    console.error("Error: reality-definitions-list element not found");
    return;
  }

  const definitions = window.evaluationData.reality_definitions;
  if (!definitions || definitions.length === 0) {
    container.innerHTML = '<p class="no-definitions">No reality definitions available.</p>';
    return;
  }

  const definitionsHtml = definitions
    .map(
      (item: RealityItem) => `
            <div class="definition-item">
                <span class="definition-id">${escapeHtml(item.id)}</span>
                <span class="definition-text">${escapeHtml(item.description)}</span>
            </div>
        `
    )
    .join("");

  container.innerHTML = definitionsHtml;
}

describe("renderAxiomDefinitions", () => {
  beforeEach(() => {
    // Set up minimal DOM structure
    document.body.innerHTML = '<div id="axiom-definitions-list"></div>';
    // Initialize window.evaluationData
    window.evaluationData = { evaluation_outputs: [] };
  });

  afterEach(() => {
    document.body.innerHTML = "";
    vi.restoreAllMocks();
  });

  it("should show no-definitions message when axiom_definitions is undefined", () => {
    window.evaluationData = { evaluation_outputs: [] };

    renderAxiomDefinitions();

    const container = document.getElementById("axiom-definitions-list");
    expect(container?.innerHTML).toContain("No axiom definitions available");
    expect(container?.querySelector(".no-definitions")).not.toBeNull();
  });

  it("should show no-definitions message when axiom_definitions is empty array", () => {
    window.evaluationData = { evaluation_outputs: [], axiom_definitions: [] };

    renderAxiomDefinitions();

    const container = document.getElementById("axiom-definitions-list");
    expect(container?.innerHTML).toContain("No axiom definitions available");
  });

  it("should render axiom definitions correctly", () => {
    window.evaluationData = {
      evaluation_outputs: [],
      axiom_definitions: [
        { id: "A-001", description: "First axiom description" },
        { id: "A-002", description: "Second axiom description" }
      ]
    };

    renderAxiomDefinitions();

    const container = document.getElementById("axiom-definitions-list");
    const items = container?.querySelectorAll(".definition-item");
    expect(items?.length).toBe(2);

    const firstItem = items?.[0];
    expect(firstItem?.querySelector(".definition-id")?.textContent).toBe("A-001");
    expect(firstItem?.querySelector(".definition-text")?.textContent).toBe(
      "First axiom description"
    );

    const secondItem = items?.[1];
    expect(secondItem?.querySelector(".definition-id")?.textContent).toBe("A-002");
    expect(secondItem?.querySelector(".definition-text")?.textContent).toBe(
      "Second axiom description"
    );
  });

  it("should log error when container element is missing", () => {
    document.body.innerHTML = ""; // Remove the container
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    renderAxiomDefinitions();

    expect(consoleSpy).toHaveBeenCalledWith("Error: axiom-definitions-list element not found");
  });
});

describe("renderRealityDefinitions", () => {
  beforeEach(() => {
    // Set up minimal DOM structure
    document.body.innerHTML = '<div id="reality-definitions-list"></div>';
    // Initialize window.evaluationData
    window.evaluationData = { evaluation_outputs: [] };
  });

  afterEach(() => {
    document.body.innerHTML = "";
    vi.restoreAllMocks();
  });

  it("should show no-definitions message when reality_definitions is undefined", () => {
    window.evaluationData = { evaluation_outputs: [] };

    renderRealityDefinitions();

    const container = document.getElementById("reality-definitions-list");
    expect(container?.innerHTML).toContain("No reality definitions available");
    expect(container?.querySelector(".no-definitions")).not.toBeNull();
  });

  it("should show no-definitions message when reality_definitions is empty array", () => {
    window.evaluationData = { evaluation_outputs: [], reality_definitions: [] };

    renderRealityDefinitions();

    const container = document.getElementById("reality-definitions-list");
    expect(container?.innerHTML).toContain("No reality definitions available");
  });

  it("should render reality definitions correctly", () => {
    window.evaluationData = {
      evaluation_outputs: [],
      reality_definitions: [
        { id: "R-001", description: "First reality item" },
        { id: "R-002", description: "Second reality item" }
      ]
    };

    renderRealityDefinitions();

    const container = document.getElementById("reality-definitions-list");
    const items = container?.querySelectorAll(".definition-item");
    expect(items?.length).toBe(2);

    const firstItem = items?.[0];
    expect(firstItem?.querySelector(".definition-id")?.textContent).toBe("R-001");
    expect(firstItem?.querySelector(".definition-text")?.textContent).toBe("First reality item");

    const secondItem = items?.[1];
    expect(secondItem?.querySelector(".definition-id")?.textContent).toBe("R-002");
    expect(secondItem?.querySelector(".definition-text")?.textContent).toBe("Second reality item");
  });

  it("should log error when container element is missing", () => {
    document.body.innerHTML = ""; // Remove the container
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    renderRealityDefinitions();

    expect(consoleSpy).toHaveBeenCalledWith("Error: reality-definitions-list element not found");
  });
});

// ============================================================================
// Reference Tag and Tooltip Tests
// ============================================================================

interface ReferenceResults {
  references_expected: string[];
  references_found: string[];
  precision: number;
  recall: number;
}

/**
 * Builds a lookup map from definitions array for quick ID-to-description lookup.
 * This is a copy of the function from script.js for testing.
 */
function buildDefinitionsMap(
  definitions: AxiomItem[] | RealityItem[] | undefined
): Map<string, string> {
  const map = new Map<string, string>();
  if (!definitions || !Array.isArray(definitions)) {
    return map;
  }
  definitions.forEach((item) => {
    const id = item.id;
    if (id && item.description) {
      map.set(id, item.description);
    }
  });
  return map;
}

/**
 * Renders a single reference tag with optional tooltip showing description.
 * This is a copy of the function from script.js for testing.
 */
function renderReferenceTag(
  refId: string,
  tagClass: string,
  definitionsMap: Map<string, string>
): string {
  const description = definitionsMap.get(refId);
  if (description) {
    const escapedDescription = description
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    return `<span class="reference-tag ${tagClass}" data-tooltip="${escapedDescription}">${refId}</span>`;
  }
  return `<span class="reference-tag ${tagClass}">${refId}</span>`;
}

/**
 * Helper to get score class - simplified version for testing
 */
function getScoreClass(score: number): string {
  if (score >= 0.8) return "score-high";
  if (score >= 0.5) return "score-medium";
  return "score-low";
}

/**
 * Renders a comparison of expected vs found references.
 * This is a copy of the function from script.js for testing.
 */
function renderReferences(
  title: string,
  references: ReferenceResults | null | undefined,
  definitionsMap?: Map<string, string>
): string {
  if (!references) {
    return "";
  }

  const defMap = definitionsMap || new Map<string, string>();
  const precisionClass = getScoreClass(references.precision);
  const recallClass = getScoreClass(references.recall);

  return `
        <div class="references-section">
            <h4>${title}</h4>
            <div class="references-grid">
                <div class="references-card">
                    <h5>Expected</h5>
                    <div class="reference-list">
                        ${
                          references.references_expected.length > 0
                            ? references.references_expected
                                .map((ref) => renderReferenceTag(ref, "expected-tag", defMap))
                                .join("")
                            : '<p style="color: #666; font-style: italic;">None expected</p>'
                        }
                    </div>
                </div>
                <div class="references-card">
                    <h5>Found in Response</h5>
                    <div class="reference-list">
                        ${
                          references.references_found.length > 0
                            ? references.references_found
                                .map((ref) => {
                                  const isMatch = references.references_expected.includes(ref);
                                  const tagClass = isMatch
                                    ? "found-match-tag"
                                    : "found-nomatch-tag";
                                  return renderReferenceTag(ref, tagClass, defMap);
                                })
                                .join("")
                            : '<p style="color: #666; font-style: italic;">None found</p>'
                        }
                    </div>
                </div>
            </div>
            <div class="references-metrics">
                <span class="score-badge ${precisionClass}">Precision: ${(references.precision * 100).toFixed(0)}%</span>
                <span class="score-badge ${recallClass}">Recall: ${(references.recall * 100).toFixed(0)}%</span>
            </div>
        </div>
    `;
}

describe("buildDefinitionsMap", () => {
  it("should return empty map for undefined definitions", () => {
    const map = buildDefinitionsMap(undefined);
    expect(map.size).toBe(0);
  });

  it("should return empty map for empty array", () => {
    const map = buildDefinitionsMap([]);
    expect(map.size).toBe(0);
  });

  it("should build map from axiom definitions", () => {
    const axioms: AxiomItem[] = [
      { id: "A-001", description: "First axiom" },
      { id: "A-002", description: "Second axiom" }
    ];
    const map = buildDefinitionsMap(axioms);

    expect(map.size).toBe(2);
    expect(map.get("A-001")).toBe("First axiom");
    expect(map.get("A-002")).toBe("Second axiom");
  });

  it("should build map from reality definitions", () => {
    const realities: RealityItem[] = [
      { id: "R-001", description: "First reality" },
      { id: "R-002", description: "Second reality" }
    ];
    const map = buildDefinitionsMap(realities);

    expect(map.size).toBe(2);
    expect(map.get("R-001")).toBe("First reality");
    expect(map.get("R-002")).toBe("Second reality");
  });

  it("should skip items without id or description", () => {
    const items = [
      { id: "A-001", description: "Valid" },
      { id: "", description: "No ID" },
      { id: "A-003", description: "" }
    ] as AxiomItem[];
    const map = buildDefinitionsMap(items);

    expect(map.size).toBe(1);
    expect(map.get("A-001")).toBe("Valid");
  });
});

describe("renderReferenceTag", () => {
  it("should render tag without tooltip when no definition exists", () => {
    const defMap = new Map<string, string>();
    const html = renderReferenceTag("A-001", "expected-tag", defMap);

    expect(html).toBe('<span class="reference-tag expected-tag">A-001</span>');
    expect(html).not.toContain("data-tooltip");
  });

  it("should render tag with tooltip when definition exists", () => {
    const defMap = new Map<string, string>([["A-001", "This is the description"]]);
    const html = renderReferenceTag("A-001", "expected-tag", defMap);

    expect(html).toContain('data-tooltip="This is the description"');
    expect(html).toContain("A-001");
    expect(html).toContain("expected-tag");
  });

  it("should escape HTML entities in tooltip", () => {
    const defMap = new Map<string, string>([["A-001", 'Test <script> & "quotes"']]);
    const html = renderReferenceTag("A-001", "expected-tag", defMap);

    expect(html).toContain("&lt;script&gt;");
    expect(html).toContain("&amp;");
    expect(html).toContain("&quot;quotes&quot;");
    expect(html).not.toContain("<script>");
  });

  it("should apply correct tag class", () => {
    const defMap = new Map<string, string>();

    expect(renderReferenceTag("A-001", "found-match-tag", defMap)).toContain("found-match-tag");
    expect(renderReferenceTag("A-001", "found-nomatch-tag", defMap)).toContain("found-nomatch-tag");
  });
});

describe("renderReferences", () => {
  it("should return empty string for null references", () => {
    expect(renderReferences("Title", null)).toBe("");
  });

  it("should return empty string for undefined references", () => {
    expect(renderReferences("Title", undefined)).toBe("");
  });

  it("should render references without definitions map", () => {
    const references: ReferenceResults = {
      references_expected: ["A-001", "A-002"],
      references_found: ["A-001"],
      precision: 1.0,
      recall: 0.5
    };

    const html = renderReferences("Axiom References", references);

    expect(html).toContain("Axiom References");
    expect(html).toContain("A-001");
    expect(html).toContain("A-002");
    expect(html).toContain("Precision: 100%");
    expect(html).toContain("Recall: 50%");
  });

  it("should render references with tooltips when definitions provided", () => {
    const references: ReferenceResults = {
      references_expected: ["A-001", "A-002"],
      references_found: ["A-001"],
      precision: 1.0,
      recall: 0.5
    };
    const defMap = new Map<string, string>([
      ["A-001", "First axiom description"],
      ["A-002", "Second axiom description"]
    ]);

    const html = renderReferences("Axiom References", references, defMap);

    expect(html).toContain('data-tooltip="First axiom description"');
    expect(html).toContain('data-tooltip="Second axiom description"');
  });

  it("should show 'None expected' when no expected references", () => {
    const references: ReferenceResults = {
      references_expected: [],
      references_found: ["A-001"],
      precision: 0,
      recall: 0
    };

    const html = renderReferences("Title", references);

    expect(html).toContain("None expected");
  });

  it("should show 'None found' when no found references", () => {
    const references: ReferenceResults = {
      references_expected: ["A-001"],
      references_found: [],
      precision: 0,
      recall: 0
    };

    const html = renderReferences("Title", references);

    expect(html).toContain("None found");
  });

  it("should apply correct tag classes for found references", () => {
    const references: ReferenceResults = {
      references_expected: ["A-001"],
      references_found: ["A-001", "A-002"],
      precision: 0.5,
      recall: 1.0
    };

    const html = renderReferences("Title", references);

    // A-001 is expected and found - should be found-match-tag
    expect(html).toContain("found-match-tag");
    // A-002 is found but not expected - should be found-nomatch-tag
    expect(html).toContain("found-nomatch-tag");
  });

  it("should only add tooltip to references that have definitions", () => {
    const references: ReferenceResults = {
      references_expected: ["A-001", "A-002"],
      references_found: [],
      precision: 0,
      recall: 0
    };
    // Only A-001 has a definition
    const defMap = new Map<string, string>([["A-001", "Has description"]]);

    const html = renderReferences("Title", references, defMap);

    // A-001 should have tooltip
    expect(html).toContain('data-tooltip="Has description"');
    // Count occurrences of data-tooltip - should be exactly 1
    const tooltipCount = (html.match(/data-tooltip/g) || []).length;
    expect(tooltipCount).toBe(1);
  });
});

// ============================================================================
// Inline Reference Highlighting Tests
// ============================================================================

/**
 * Highlights axiom and reality references in text by wrapping them with tooltip spans.
 * This is a copy of the function from script.js for testing.
 */
function highlightReferencesInText(
  text: string | null | undefined,
  axiomDefinitionsMap: Map<string, string>,
  realityDefinitionsMap: Map<string, string>
): string {
  if (!text) {
    return text ?? "";
  }

  // Match patterns like [A-001], [A-002], [R-001], [R-002], etc.
  const referencePattern = /\[(A-\d{1,4}|R-\d{1,4})\]/g;

  return text.replace(referencePattern, (match, refId: string) => {
    const isAxiom = refId.startsWith("A-");
    const definitionsMap = isAxiom ? axiomDefinitionsMap : realityDefinitionsMap;
    const description = definitionsMap.get(refId);

    if (description) {
      const escapedDescription = escapeHtml(description);
      const tagClass = isAxiom ? "inline-axiom-ref" : "inline-reality-ref";
      return `<span class="inline-reference ${tagClass}" data-tooltip="${escapedDescription}" tabindex="0">[${refId}]</span>`;
    }
    // If no description found, return the match unchanged
    return match;
  });
}

describe("highlightReferencesInText", () => {
  it("should return empty string for null text", () => {
    const axiomMap = new Map<string, string>();
    const realityMap = new Map<string, string>();
    expect(highlightReferencesInText(null, axiomMap, realityMap)).toBe("");
  });

  it("should return empty string for undefined text", () => {
    const axiomMap = new Map<string, string>();
    const realityMap = new Map<string, string>();
    expect(highlightReferencesInText(undefined, axiomMap, realityMap)).toBe("");
  });

  it("should return text unchanged when no references found", () => {
    const axiomMap = new Map<string, string>();
    const realityMap = new Map<string, string>();
    const text = "This is a text without any references.";
    expect(highlightReferencesInText(text, axiomMap, realityMap)).toBe(text);
  });

  it("should highlight axiom references with tooltips", () => {
    const axiomMap = new Map<string, string>([["A-001", "First axiom description"]]);
    const realityMap = new Map<string, string>();
    const text = "According to [A-001], this is true.";

    const result = highlightReferencesInText(text, axiomMap, realityMap);

    expect(result).toContain('class="inline-reference inline-axiom-ref"');
    expect(result).toContain('data-tooltip="First axiom description"');
    expect(result).toContain("[A-001]");
    expect(result).toContain('tabindex="0"');
  });

  it("should highlight reality references with tooltips", () => {
    const axiomMap = new Map<string, string>();
    const realityMap = new Map<string, string>([["R-001", "First reality description"]]);
    const text = "Based on [R-001], the balance is correct.";

    const result = highlightReferencesInText(text, axiomMap, realityMap);

    expect(result).toContain('class="inline-reference inline-reality-ref"');
    expect(result).toContain('data-tooltip="First reality description"');
    expect(result).toContain("[R-001]");
  });

  it("should highlight both axiom and reality references in the same text", () => {
    const axiomMap = new Map<string, string>([["A-001", "Axiom description"]]);
    const realityMap = new Map<string, string>([["R-001", "Reality description"]]);
    const text = "According to [A-001] and [R-001], the answer is correct.";

    const result = highlightReferencesInText(text, axiomMap, realityMap);

    expect(result).toContain("inline-axiom-ref");
    expect(result).toContain("inline-reality-ref");
    expect(result).toContain('data-tooltip="Axiom description"');
    expect(result).toContain('data-tooltip="Reality description"');
  });

  it("should leave references unchanged when no definition exists", () => {
    const axiomMap = new Map<string, string>();
    const realityMap = new Map<string, string>();
    const text = "Reference [A-999] has no definition.";

    const result = highlightReferencesInText(text, axiomMap, realityMap);

    expect(result).toBe(text);
    expect(result).not.toContain("inline-reference");
    expect(result).not.toContain("data-tooltip");
  });

  it("should handle multiple references of the same type", () => {
    const axiomMap = new Map<string, string>([
      ["A-001", "First axiom"],
      ["A-002", "Second axiom"]
    ]);
    const realityMap = new Map<string, string>();
    const text = "See [A-001] and [A-002] for details.";

    const result = highlightReferencesInText(text, axiomMap, realityMap);

    const tooltipCount = (result.match(/data-tooltip/g) || []).length;
    expect(tooltipCount).toBe(2);
    expect(result).toContain('data-tooltip="First axiom"');
    expect(result).toContain('data-tooltip="Second axiom"');
  });

  it("should escape HTML in descriptions", () => {
    const axiomMap = new Map<string, string>([["A-001", '<script>alert("XSS")</script>']]);
    const realityMap = new Map<string, string>();
    const text = "Check [A-001] for security.";

    const result = highlightReferencesInText(text, axiomMap, realityMap);

    expect(result).toContain("&lt;script&gt;");
    expect(result).not.toContain("<script>");
    expect(result).toContain("&quot;XSS&quot;");
  });

  it("should handle references with various number formats", () => {
    const axiomMap = new Map<string, string>([
      ["A-1", "Single digit"],
      ["A-01", "Two digits"],
      ["A-001", "Three digits"],
      ["A-0001", "Four digits"]
    ]);
    const realityMap = new Map<string, string>();
    const text = "[A-1] [A-01] [A-001] [A-0001]";

    const result = highlightReferencesInText(text, axiomMap, realityMap);

    expect((result.match(/data-tooltip/g) || []).length).toBe(4);
  });

  it("should only match bracketed references", () => {
    const axiomMap = new Map<string, string>([["A-001", "Description"]]);
    const realityMap = new Map<string, string>();
    const text = "A-001 without brackets should not match, but [A-001] should.";

    const result = highlightReferencesInText(text, axiomMap, realityMap);

    // Only one tooltip should be added (for the bracketed reference)
    const tooltipCount = (result.match(/data-tooltip/g) || []).length;
    expect(tooltipCount).toBe(1);
  });
});

// ============================================================================
// Entity Highlighting and Integration Tests
// ============================================================================

/** @type {Map<string, number>} Maps entity names to their assigned color index for testing */
const testEntityColorMap = new Map<string, number>();
let testColorIndex = 0;

/**
 * Gets or assigns a consistent color index for a given entity (test version).
 */
function getEntityColor(entity: string): number {
  if (!testEntityColorMap.has(entity)) {
    testEntityColorMap.set(entity, testColorIndex % 20);
    testColorIndex++;
  }
  return testEntityColorMap.get(entity) ?? 0;
}

/**
 * Converts line break characters to HTML <br> tags.
 * This is a simplified copy of the function from script.js for testing.
 */
function convertLineBreaks(text: string | null | undefined): string {
  if (!text) return text ?? "";
  return text
    .replace(/\r\n/g, "<br>")
    .replace(/\n/g, "<br>")
    .replace(/\r/g, "<br>")
    .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>");
}

/**
 * Highlights entities in text by wrapping them with colored spans.
 * Also highlights axiom/reality references with tooltips if definition maps are provided.
 * This is a copy of the function from script.js for testing.
 */
function highlightEntitiesInText(
  text: string | null | undefined,
  entities: string[] | null | undefined,
  axiomDefinitionsMap?: Map<string, string>,
  realityDefinitionsMap?: Map<string, string>
): string {
  if (!text || !entities || entities.length === 0) {
    // Still apply reference highlighting even if no entities
    let result = text ?? "";
    if (axiomDefinitionsMap && realityDefinitionsMap) {
      result = highlightReferencesInText(result, axiomDefinitionsMap, realityDefinitionsMap);
    }
    return convertLineBreaks(result);
  }

  let highlightedText = text;

  // FIRST: Highlight entities in plain text (before any HTML is added)
  // Sort entities by length (longest first) to avoid partial matches
  const sortedEntities = [...entities].sort((a, b) => b.length - a.length);

  sortedEntities.forEach((entity) => {
    const colorClass = `entity-color-${getEntityColor(entity)}`;
    // Create a case-insensitive regex that matches whole words
    const regex = new RegExp(`\\b${entity.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "gi");
    highlightedText = highlightedText.replace(
      regex,
      `<span class="entity-highlight ${colorClass}">${entity}</span>`
    );
  });

  // SECOND: Highlight axiom/reality references AFTER entity highlighting
  // This ensures we don't match entities inside tooltip data-attributes
  if (axiomDefinitionsMap && realityDefinitionsMap) {
    highlightedText = highlightReferencesInText(
      highlightedText,
      axiomDefinitionsMap,
      realityDefinitionsMap
    );
  }

  return convertLineBreaks(highlightedText);
}

describe("highlightEntitiesInText", () => {
  beforeEach(() => {
    // Reset color map between tests for predictable results
    testEntityColorMap.clear();
    testColorIndex = 0;
  });

  it("should return text with line breaks converted when no entities", () => {
    const text = "Hello\nWorld";
    const result = highlightEntitiesInText(text, []);
    expect(result).toBe("Hello<br>World");
  });

  it("should return empty string for null text", () => {
    const result = highlightEntitiesInText(null, ["entity"]);
    expect(result).toBe("");
  });

  it("should return empty string for undefined text", () => {
    const result = highlightEntitiesInText(undefined, ["entity"]);
    expect(result).toBe("");
  });

  it("should highlight a single entity", () => {
    const text = "The market stability is important.";
    const entities = ["market stability"];

    const result = highlightEntitiesInText(text, entities);

    expect(result).toContain('class="entity-highlight');
    expect(result).toContain("market stability");
  });

  it("should highlight multiple entities with different colors", () => {
    const text = "Political instability affects investor confidence.";
    const entities = ["political instability", "investor confidence"];

    const result = highlightEntitiesInText(text, entities);

    expect(result).toContain("entity-color-0");
    expect(result).toContain("entity-color-1");
  });

  it("should be case-insensitive when matching entities", () => {
    const text = "MARKET STABILITY and Market Stability both matter.";
    const entities = ["market stability"];

    const result = highlightEntitiesInText(text, entities);

    // Both occurrences should be highlighted
    const highlightCount = (result.match(/entity-highlight/g) || []).length;
    expect(highlightCount).toBe(2);
  });

  it("should match whole words only", () => {
    const text = "The markets are unstable, but market stability is key.";
    const entities = ["market"];

    const result = highlightEntitiesInText(text, entities);

    // Should only match "market" not "markets"
    const highlightCount = (result.match(/entity-highlight/g) || []).length;
    expect(highlightCount).toBe(1);
  });

  it("should sort entities by length to avoid partial matches", () => {
    const text = "The central bank interest rate affects the interest rate.";
    const entities = ["interest rate", "central bank interest rate"];

    const result = highlightEntitiesInText(text, entities);

    // Longer entity "central bank interest rate" should be processed first
    // Both entities should be highlighted
    expect(result).toContain("entity-highlight");
    expect(result).toContain("interest rate</span>");
    // The sorting ensures longer matches are attempted first to minimize nesting issues
    const highlightCount = (result.match(/entity-highlight/g) || []).length;
    expect(highlightCount).toBeGreaterThanOrEqual(2);
  });
});

describe("highlightEntitiesInText with References - Integration Tests", () => {
  beforeEach(() => {
    testEntityColorMap.clear();
    testColorIndex = 0;
  });

  it("should highlight both entities and references in the same text", () => {
    const text = "Political instability [A-001] affects market stability.";
    const entities = ["political instability", "market stability"];
    const axiomMap = new Map<string, string>([["A-001", "Political instability disrupts markets"]]);
    const realityMap = new Map<string, string>();

    const result = highlightEntitiesInText(text, entities, axiomMap, realityMap);

    // Check entities are highlighted
    expect(result).toContain("entity-highlight");
    expect(result).toContain("political instability");
    expect(result).toContain("market stability");

    // Check reference is highlighted with tooltip
    expect(result).toContain("inline-reference");
    expect(result).toContain("inline-axiom-ref");
    expect(result).toContain("data-tooltip");
  });

  it("should not break reference matching when entity names contain letters A or R", () => {
    const text = "According to [A-001], Area R development affects Region A.";
    const entities = ["Area R", "Region A"];
    const axiomMap = new Map<string, string>([["A-001", "Development axiom"]]);
    const realityMap = new Map<string, string>();

    const result = highlightEntitiesInText(text, entities, axiomMap, realityMap);

    // Reference should still be highlighted correctly
    expect(result).toContain('data-tooltip="Development axiom"');
    expect(result).toContain("[A-001]");

    // Entities should be highlighted
    expect(result).toContain("Area R</span>");
    expect(result).toContain("Region A</span>");
  });

  it("should not break reference matching when entity names contain numbers", () => {
    const text = "Product 001 is referenced in [A-001] and [R-002].";
    const entities = ["Product 001"];
    const axiomMap = new Map<string, string>([["A-001", "First axiom"]]);
    const realityMap = new Map<string, string>([["R-002", "Second reality"]]);

    const result = highlightEntitiesInText(text, entities, axiomMap, realityMap);

    // Both references should be highlighted with tooltips
    expect(result).toContain('data-tooltip="First axiom"');
    expect(result).toContain('data-tooltip="Second reality"');

    // Entity should also be highlighted
    expect(result).toContain("Product 001</span>");
  });

  it("should highlight entities even if they match reference ID patterns", () => {
    // KNOWN LIMITATION: When an entity name matches a reference ID (e.g., "A-001"),
    // the entity highlighting will wrap the ID inside [A-001], breaking the reference
    // pattern matching. This is acceptable because:
    // 1. Entity names matching reference IDs (A-XXX, R-XXX) are rare in practice
    // 2. The unbracketed instance will still be highlighted as an entity
    const text = "The code A-001 is different from [A-001] which is a reference.";
    const entities = ["A-001"];
    const axiomMap = new Map<string, string>([["A-001", "Axiom description"]]);
    const realityMap = new Map<string, string>();

    const result = highlightEntitiesInText(text, entities, axiomMap, realityMap);

    // Both occurrences of A-001 (inside and outside brackets) are highlighted as entities
    const entityHighlightCount = (result.match(/entity-highlight/g) || []).length;
    expect(entityHighlightCount).toBe(2);

    // Note: The reference tooltip will NOT be applied because entity highlighting
    // breaks the [A-001] pattern into [<span>A-001</span>]
    // This documents the current behavior as a known limitation
    expect(result).not.toContain('data-tooltip="Axiom description"');
  });

  it("should apply reference highlighting even when entities array is empty", () => {
    const text = "See [A-001] and [R-001] for details.";
    const entities: string[] = [];
    const axiomMap = new Map<string, string>([["A-001", "Axiom one"]]);
    const realityMap = new Map<string, string>([["R-001", "Reality one"]]);

    const result = highlightEntitiesInText(text, entities, axiomMap, realityMap);

    expect(result).toContain('data-tooltip="Axiom one"');
    expect(result).toContain('data-tooltip="Reality one"');
  });

  it("should not match entities inside reference tooltip attributes", () => {
    // This is the key integration test - entity highlighting runs first,
    // so entities should not be found inside the tooltip text that's added later
    const text = "Based on [A-001], political instability is a concern.";
    const entities = ["political instability"];
    const axiomMap = new Map<string, string>([
      ["A-001", "Political instability often disrupts markets"]
    ]);
    const realityMap = new Map<string, string>();

    const result = highlightEntitiesInText(text, entities, axiomMap, realityMap);

    // The tooltip should contain the full description without entity spans inside it
    expect(result).toContain('data-tooltip="Political instability often disrupts markets"');

    // The entity in the main text should be highlighted
    expect(result).toContain(
      '<span class="entity-highlight entity-color-0">political instability</span>'
    );

    // There should be no entity-highlight inside the data-tooltip attribute
    expect(result).not.toMatch(/data-tooltip="[^"]*entity-highlight[^"]*"/);
  });

  it("should handle complex text with multiple entities and references", () => {
    const text =
      "According to [A-001], political instability disrupts investor confidence. " +
      "See also [R-001] for current inflation data affecting market stability.";
    const entities = ["political instability", "investor confidence", "market stability"];
    const axiomMap = new Map<string, string>([["A-001", "Instability disrupts markets"]]);
    const realityMap = new Map<string, string>([["R-001", "Current inflation is 2.1%"]]);

    const result = highlightEntitiesInText(text, entities, axiomMap, realityMap);

    // All entities should be highlighted
    expect(result).toContain("political instability</span>");
    expect(result).toContain("investor confidence</span>");
    expect(result).toContain("market stability</span>");

    // Both references should have tooltips
    expect(result).toContain('data-tooltip="Instability disrupts markets"');
    expect(result).toContain('data-tooltip="Current inflation is 2.1%"');

    // References should have correct classes
    expect(result).toContain("inline-axiom-ref");
    expect(result).toContain("inline-reality-ref");
  });

  it("should convert line breaks in the final output", () => {
    const text = "Line 1\nLine 2 with [A-001]";
    const entities = ["Line 1"];
    const axiomMap = new Map<string, string>([["A-001", "Axiom"]]);
    const realityMap = new Map<string, string>();

    const result = highlightEntitiesInText(text, entities, axiomMap, realityMap);

    expect(result).toContain("<br>");
    expect(result).not.toContain("\n");
  });

  it("should handle markdown bold formatting", () => {
    const text = "This is **important** text with [A-001].";
    const entities: string[] = [];
    const axiomMap = new Map<string, string>([["A-001", "Axiom"]]);
    const realityMap = new Map<string, string>();

    const result = highlightEntitiesInText(text, entities, axiomMap, realityMap);

    expect(result).toContain("<b>important</b>");
    expect(result).not.toContain("**important**");
  });
});

// ============================================================================
// Edge Case Tests - Null, Undefined, and Empty Arrays
// ============================================================================

describe("Edge Cases - buildDefinitionsMap", () => {
  it("should handle null definitions gracefully", () => {
    const map = buildDefinitionsMap(null as unknown as AxiomItem[]);
    expect(map.size).toBe(0);
  });

  it("should handle non-array input gracefully", () => {
    const map = buildDefinitionsMap("not an array" as unknown as AxiomItem[]);
    expect(map.size).toBe(0);
  });

  it("should handle items with null id", () => {
    const items = [
      { id: null, description: "Has null ID" },
      { id: "A-001", description: "Valid" }
    ] as unknown as AxiomItem[];
    const map = buildDefinitionsMap(items);

    expect(map.size).toBe(1);
    expect(map.get("A-001")).toBe("Valid");
  });

  it("should handle items with null description", () => {
    const items = [
      { id: "A-001", description: null },
      { id: "A-002", description: "Valid" }
    ] as unknown as AxiomItem[];
    const map = buildDefinitionsMap(items);

    expect(map.size).toBe(1);
    expect(map.get("A-002")).toBe("Valid");
  });

  it("should handle items with undefined fields", () => {
    const items = [
      { id: undefined, description: "No ID" },
      { description: "Missing ID field entirely" },
      { id: "A-001" } // Missing description
    ] as unknown as AxiomItem[];
    const map = buildDefinitionsMap(items);

    expect(map.size).toBe(0);
  });
});

describe("Edge Cases - renderReferenceTag", () => {
  it("should handle empty string refId", () => {
    const defMap = new Map<string, string>();
    const html = renderReferenceTag("", "expected-tag", defMap);

    expect(html).toBe('<span class="reference-tag expected-tag"></span>');
  });

  it("should handle empty definitions map", () => {
    const defMap = new Map<string, string>();
    const html = renderReferenceTag("A-001", "expected-tag", defMap);

    expect(html).not.toContain("data-tooltip");
  });

  it("should handle special characters in refId", () => {
    const defMap = new Map<string, string>();
    const html = renderReferenceTag("A-001<test>", "expected-tag", defMap);

    // The refId is rendered as-is (no XSS protection in ID, only in tooltip)
    expect(html).toContain("A-001<test>");
  });

  it("should handle newlines in description", () => {
    const defMap = new Map<string, string>([["A-001", "Line 1\nLine 2"]]);
    const html = renderReferenceTag("A-001", "expected-tag", defMap);

    expect(html).toContain("data-tooltip");
    expect(html).toContain("Line 1");
  });
});

describe("Edge Cases - renderReferences", () => {
  it("should handle references with empty arrays for both expected and found", () => {
    const references: ReferenceResults = {
      references_expected: [],
      references_found: [],
      precision: 0,
      recall: 0
    };

    const html = renderReferences("Title", references);

    expect(html).toContain("None expected");
    expect(html).toContain("None found");
  });

  it("should handle precision and recall of exactly 0", () => {
    const references: ReferenceResults = {
      references_expected: ["A-001"],
      references_found: ["A-002"],
      precision: 0,
      recall: 0
    };

    const html = renderReferences("Title", references);

    expect(html).toContain("Precision: 0%");
    expect(html).toContain("Recall: 0%");
  });

  it("should handle decimal precision values correctly", () => {
    const references: ReferenceResults = {
      references_expected: ["A-001", "A-002", "A-003"],
      references_found: ["A-001"],
      precision: 1.0,
      recall: 0.333
    };

    const html = renderReferences("Title", references);

    expect(html).toContain("Precision: 100%");
    expect(html).toContain("Recall: 33%");
  });
});

// ============================================================================
// Collapsible Definitions Section Tests
// ============================================================================

/**
 * Toggles the collapsed/expanded state of a definitions section.
 * This is a copy of the function from script.js for testing.
 */
function toggleDefinitionsSection(headerElement: HTMLElement): void {
  const content = headerElement.nextElementSibling;
  const isCollapsed = headerElement.classList.contains("collapsed");

  if (isCollapsed) {
    headerElement.classList.remove("collapsed");
    content?.classList.remove("collapsed");
    headerElement.setAttribute("aria-expanded", "true");
  } else {
    headerElement.classList.add("collapsed");
    content?.classList.add("collapsed");
    headerElement.setAttribute("aria-expanded", "false");
  }
}

describe("toggleDefinitionsSection", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div class="definitions-section">
        <div class="definitions-header" role="button" tabindex="0" aria-expanded="true">
          <h2>Test Section</h2>
          <span class="toggle-icon">▼</span>
        </div>
        <div class="definitions-content">
          <p>Content here</p>
        </div>
      </div>
    `;
  });

  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("should collapse an expanded section", () => {
    const header = document.querySelector(".definitions-header") as HTMLElement;
    const content = document.querySelector(".definitions-content") as HTMLElement;

    expect(header.classList.contains("collapsed")).toBe(false);
    expect(content.classList.contains("collapsed")).toBe(false);

    toggleDefinitionsSection(header);

    expect(header.classList.contains("collapsed")).toBe(true);
    expect(content.classList.contains("collapsed")).toBe(true);
    expect(header.getAttribute("aria-expanded")).toBe("false");
  });

  it("should expand a collapsed section", () => {
    const header = document.querySelector(".definitions-header") as HTMLElement;
    const content = document.querySelector(".definitions-content") as HTMLElement;

    // First collapse
    header.classList.add("collapsed");
    content.classList.add("collapsed");
    header.setAttribute("aria-expanded", "false");

    toggleDefinitionsSection(header);

    expect(header.classList.contains("collapsed")).toBe(false);
    expect(content.classList.contains("collapsed")).toBe(false);
    expect(header.getAttribute("aria-expanded")).toBe("true");
  });

  it("should toggle aria-expanded attribute correctly", () => {
    const header = document.querySelector(".definitions-header") as HTMLElement;

    expect(header.getAttribute("aria-expanded")).toBe("true");

    toggleDefinitionsSection(header);
    expect(header.getAttribute("aria-expanded")).toBe("false");

    toggleDefinitionsSection(header);
    expect(header.getAttribute("aria-expanded")).toBe("true");
  });
});

describe("Edge Cases - renderAxiomDefinitions", () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="axiom-definitions-list"></div>';
    window.evaluationData = { evaluation_outputs: [] };
  });

  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("should handle null axiom_definitions", () => {
    window.evaluationData = {
      evaluation_outputs: [],
      axiom_definitions: null as unknown as AxiomItem[]
    };

    renderAxiomDefinitions();

    const container = document.getElementById("axiom-definitions-list");
    expect(container?.innerHTML).toContain("No axiom definitions available");
  });

  it("should handle axiom definitions with special characters", () => {
    window.evaluationData = {
      evaluation_outputs: [],
      axiom_definitions: [
        { id: "A-001", description: "Description with <script>alert('xss')</script>" }
      ]
    };

    renderAxiomDefinitions();

    const container = document.getElementById("axiom-definitions-list");
    const descriptionElement = container?.querySelector(".definition-text");
    // Verify that the description is escaped and not executed
    expect(descriptionElement?.innerHTML).toContain("&lt;script&gt;");
    expect(descriptionElement?.innerHTML).not.toContain("<script>");
    expect(descriptionElement?.innerHTML).toContain("&lt;/script&gt;");
  });
});

describe("Edge Cases - renderRealityDefinitions", () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="reality-definitions-list"></div>';
    window.evaluationData = { evaluation_outputs: [] };
  });

  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("should handle null reality_definitions", () => {
    window.evaluationData = {
      evaluation_outputs: [],
      reality_definitions: null as unknown as RealityItem[]
    };

    renderRealityDefinitions();

    const container = document.getElementById("reality-definitions-list");
    expect(container?.innerHTML).toContain("No reality definitions available");
  });

  it("should handle reality definitions with long descriptions", () => {
    const longDescription = "A".repeat(1000);
    window.evaluationData = {
      evaluation_outputs: [],
      reality_definitions: [{ id: "R-001", description: longDescription }]
    };

    renderRealityDefinitions();

    const container = document.getElementById("reality-definitions-list");
    const textElement = container?.querySelector(".definition-text");
    expect(textElement?.textContent).toBe(longDescription);
  });

  it("should handle reality definitions with special characters", () => {
    window.evaluationData = {
      evaluation_outputs: [],
      reality_definitions: [
        { id: "R-001", description: "Description with <script>alert('xss')</script>" }
      ]
    };

    renderRealityDefinitions();

    const container = document.getElementById("reality-definitions-list");
    const descriptionElement = container?.querySelector(".definition-text");
    // Verify that the description is escaped and not executed
    expect(descriptionElement?.innerHTML).toContain("&lt;script&gt;");
    expect(descriptionElement?.innerHTML).not.toContain("<script>");
    expect(descriptionElement?.innerHTML).toContain("&lt;/script&gt;");
  });
});
