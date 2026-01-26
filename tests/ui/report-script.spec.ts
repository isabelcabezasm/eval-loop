/**
 * Tests for report generation script functions.
 * Uses jsdom environment to test DOM manipulation functions.
 * @vitest-environment jsdom
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Type definitions matching script.js JSDoc types
interface AxiomItem {
  axiom_id: string;
  description: string;
}

interface RealityItem {
  reality_id: string;
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
                <span class="definition-id">${item.axiom_id}</span>
                <span class="definition-text">${item.description}</span>
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
                <span class="definition-id">${item.reality_id}</span>
                <span class="definition-text">${item.description}</span>
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
        { axiom_id: "A-001", description: "First axiom description" },
        { axiom_id: "A-002", description: "Second axiom description" }
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
        { reality_id: "R-001", description: "First reality item" },
        { reality_id: "R-002", description: "Second reality item" }
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
    const id = (item as AxiomItem).axiom_id || (item as RealityItem).reality_id;
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
      { axiom_id: "A-001", description: "First axiom" },
      { axiom_id: "A-002", description: "Second axiom" }
    ];
    const map = buildDefinitionsMap(axioms);

    expect(map.size).toBe(2);
    expect(map.get("A-001")).toBe("First axiom");
    expect(map.get("A-002")).toBe("Second axiom");
  });

  it("should build map from reality definitions", () => {
    const realities: RealityItem[] = [
      { reality_id: "R-001", description: "First reality" },
      { reality_id: "R-002", description: "Second reality" }
    ];
    const map = buildDefinitionsMap(realities);

    expect(map.size).toBe(2);
    expect(map.get("R-001")).toBe("First reality");
    expect(map.get("R-002")).toBe("Second reality");
  });

  it("should skip items without id or description", () => {
    const items = [
      { axiom_id: "A-001", description: "Valid" },
      { axiom_id: "", description: "No ID" },
      { axiom_id: "A-003", description: "" }
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
