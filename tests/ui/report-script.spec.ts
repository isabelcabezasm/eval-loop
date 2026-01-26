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
        const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => { });

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
        const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => { });

        renderRealityDefinitions();

        expect(consoleSpy).toHaveBeenCalledWith("Error: reality-definitions-list element not found");
    });
});
