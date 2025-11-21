// Global entity color mapping
const entityColorMap = new Map();
let colorIndex = 0;

/**
 * Gets or assigns a consistent color index for a given entity.
 * Colors are assigned sequentially and cycle through 20 available colors.
 * @param {string} entity - The entity name to get a color for
 * @returns {number} The color index (0-19) for the entity
 */
function getEntityColor(entity) {
    if (!entityColorMap.has(entity)) {
        entityColorMap.set(entity, colorIndex % 20);
        colorIndex++;
    }
    return entityColorMap.get(entity);
}

/**
 * Determines the CSS class name based on a score value.
 * Used for color-coding scores as good (green), medium (yellow), or poor (red).
 * @param {number} score - The score value between 0 and 1
 * @returns {string} CSS class name: 'score-good', 'score-medium', or 'score-poor'
 */
function getScoreClass(score) {
    if (score >= 0.7) return 'score-good';
    if (score >= 0.4) return 'score-medium';
    return 'score-poor';
}

/**
 * Converts line break characters to HTML <br> tags and markdown bold to HTML <b> tags.
 * Handles various line break formats (CRLF, LF, CR) for cross-platform compatibility.
 * @param {string} text - The text to convert
 * @returns {string} HTML-formatted text with line breaks and bold formatting
 */
function convertLineBreaks(text) {
    if (!text) return text;
    return text
        .replace(/\r\n/g, '<br>')
        .replace(/\n/g, '<br>')
        .replace(/\r/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
}

/**
 * Formats reasoning text for display, handling both array and string formats.
 * Arrays are converted to HTML unordered lists, strings are formatted with line breaks.
 * @param {string|Array<string>} reasoning - The reasoning text to format
 * @returns {string} HTML-formatted reasoning text
 */
function formatReasoning(reasoning) {
    if (Array.isArray(reasoning)) {
        return '<ul>' + reasoning.map(item =>
            `<li>${convertLineBreaks(item)}</li>`).join('') + '</ul>';
    }
    return convertLineBreaks(reasoning);
}

/**
 * Searches for entities in text using case-insensitive whole-word matching.
 * Only returns entities that are found as complete words in the text.
 * @param {string} text - The text to search in
 * @param {Array<string>} entities - Array of entity strings to search for
 * @returns {Array<string>} Array of entities found in the text
 */
function findEntitiesInText(text, entities) {
    if (!text || !entities || entities.length === 0) {
        return [];
    }

    const foundEntities = [];
    entities.forEach(entity => {
        // Create a case-insensitive regex that matches whole words
        const regex = new RegExp(
            `\\b${entity.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`,
            'gi'
        );
        if (regex.test(text)) {
            foundEntities.push(entity);
        }
    });

    return foundEntities;
}

/**
 * Highlights entities in text by wrapping them with colored spans.
 * Entities are sorted by length (longest first) to avoid partial matches.
 * Each entity gets a consistent color based on its assigned color index.
 * @param {string} text - The text to highlight entities in
 * @param {Array<string>} entities - Array of entity strings to highlight
 * @returns {string} HTML text with highlighted entities and converted line breaks
 */
function highlightEntitiesInText(text, entities) {
    if (!text || !entities || entities.length === 0) {
        return convertLineBreaks(text);
    }

    let highlightedText = text;

    // Sort entities by length (longest first) to avoid partial matches
    const sortedEntities = [...entities].sort((a, b) => b.length - a.length);

    sortedEntities.forEach(entity => {
        const colorClass = `entity-color-${getEntityColor(entity)}`;
        // Create a case-insensitive regex that matches whole words
        const regex = new RegExp(
            `\\b${entity.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`,
            'gi'
        );
        highlightedText = highlightedText.replace(
            regex,
            `<span class="entity-highlight ${colorClass}">${entity}</span>`
        );
    });

    return convertLineBreaks(highlightedText);
}

/**
 * Renders a list of axioms as styled tags in an HTML section.
 * Returns an empty string if no axioms are provided.
 * @param {Array<string>} axioms - Array of axiom strings to display
 * @returns {string} HTML string containing the axioms section, or empty string if no axioms
 */
function renderAxioms(axioms) {
    if (!axioms || axioms.length === 0) {
        return '';
    }

    return `
        <div class="axioms">
            <h4>Related Axioms</h4>
            <div class="axiom-list">
                ${axioms.map(axiom => `
                    <span class="axiom-tag">${axiom}</span>
                `).join('')}
            </div>
        </div>
    `;
}

/**
 * Renders entity information in a three-column grid layout.
 * Displays query entities, expected answer entities, and LLM answer entities.
 * Each entity pair shows trigger variable → consequence variable with consistent colors.
 * @param {Object} entities - Object containing three arrays of entity pairs
 * @param {Array} entities.user_query_entities - Entities from user query
 * @param {Array} entities.expected_answer_entities - Entities from expected answer
 * @param {Array} entities.llm_answer_entities - Entities from LLM response
 * @returns {string} HTML string containing the entities grid layout
 */
function renderEntities(entities) {
    return `
        <div class="entities">
            <h4>Identified Entities</h4>
            <div class="entity-grid">
                <div class="entity-card">
                    <h5>Query Entities</h5>
                    <div class="entity-list">
                        ${entities.user_query_entities.length > 0 ?
            entities.user_query_entities.map(entity => `
                            <div class="entity-pair">
                                <span class="entity-tag entity-color-${getEntityColor(entity.trigger_variable)
                }">${entity.trigger_variable}</span>
                                <span style="color: #666; margin: 0 5px;">
                                    →
                                </span>
                                <span class="entity-tag entity-color-${getEntityColor(entity.consequence_variable)
                }">${entity.consequence_variable}</span>
                            </div>
                        `).join('') :
            '<p style="color: #666; font-style: italic;">' +
            'No entities identified</p>'}
                    </div>
                </div>
                <div class="entity-card">
                    <h5>Expected Answer Entities</h5>
                    <div class="entity-list">
                        ${entities.expected_answer_entities.length > 0 ?
            entities.expected_answer_entities.map(entity => `
                            <div class="entity-pair">
                                <span class="entity-tag entity-color-${getEntityColor(entity.trigger_variable)
                }">${entity.trigger_variable}</span>
                                <span style="color: #666; margin: 0 5px;">
                                    →
                                </span>
                                <span class="entity-tag entity-color-${getEntityColor(entity.consequence_variable)
                }">${entity.consequence_variable}</span>
                            </div>
                        `).join('') :
            '<p style="color: #666; font-style: italic;">' +
            'No entities identified</p>'}
                    </div>
                </div>
                <div class="entity-card">
                    <h5>LLM Answer Entities</h5>
                    <div class="entity-list">
                        ${entities.llm_answer_entities.length > 0 ?
            entities.llm_answer_entities.map(entity => `
                            <div class="entity-pair">
                                <span class="entity-tag entity-color-${getEntityColor(entity.trigger_variable)
                }">${entity.trigger_variable}</span>
                                <span style="color: #666; margin: 0 5px;">
                                    →
                                </span>
                                <span class="entity-tag entity-color-${getEntityColor(entity.consequence_variable)
                }">${entity.consequence_variable}</span>
                            </div>
                        `).join('') :
            '<p style="color: #666; font-style: italic;">' +
            'No entities identified</p>'}
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Renders detailed accuracy information showing entity-level scores and reasons.
 * Displays each entity's accuracy score as a percentage with explanatory text.
 * @param {Object} accuracy - Accuracy object containing entity_accuracies array
 * @param {Array} accuracy.entity_accuracies - Array of entity accuracy results
 * @returns {string} HTML string containing the accuracy details section
 */
function renderAccuracyDetails(accuracy) {
    return `
        <div class="accuracy-details">
            <h5>Entity-Level Accuracy</h5>
            ${accuracy.entity_accuracies.map(result => `
                <div class="accuracy-result">
                    <div>
                        <div class="accuracy-entity">
                            ${result.entity}
                        </div>
                        <div class="accuracy-reason">
                            ${convertLineBreaks(result.reason)}
                        </div>
                    </div>
                    <div class="accuracy-score">
                        ${(result.score * 100).toFixed(0)}%
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

/**
 * Renders a complete evaluation item with collapsible content.
 * Includes query, expected/LLM responses with entity highlighting, scores, and detailed analysis.
 * Only highlights entities that appear in both expected and LLM responses for clarity.
 * @param {Object} evaluation - Complete evaluation object containing input, responses, and scores
 * @returns {string} HTML string containing the full evaluation display
 */
function renderEvaluation(evaluation) {
    const accuracyClass = getScoreClass(evaluation.accuracy.accuracy_mean);
    const coverageClass = getScoreClass(
        evaluation.topic_coverage.coverage_score
    );

    // Collect all entities for analysis
    const allEntityValues = [];

    // Extract trigger and consequence variables from all entity objects
    [evaluation.entities.user_query_entities,
    evaluation.entities.llm_answer_entities,
    evaluation.entities.expected_answer_entities].forEach(entityList => {
        if (Array.isArray(entityList)) {
            entityList.forEach(entity => {
                if (entity.trigger_variable) {
                    allEntityValues.push(entity.trigger_variable);
                }
                if (entity.consequence_variable) {
                    allEntityValues.push(entity.consequence_variable);
                }
            });
        }
    });

    // Remove duplicates
    const uniqueEntities = [...new Set(allEntityValues)];

    // Find entities that exist in both texts
    const entitiesInExpected = findEntitiesInText(
        evaluation.input.expected_answer,
        uniqueEntities
    );
    const entitiesInLlm = findEntitiesInText(
        evaluation.llm_response,
        uniqueEntities
    );

    // Only highlight entities that appear in BOTH texts
    const commonEntities = entitiesInExpected.filter(entity =>
        entitiesInLlm.includes(entity)
    );

    // Highlight only common entities in response texts
    const highlightedExpectedAnswer = highlightEntitiesInText(
        evaluation.input.expected_answer,
        commonEntities
    );
    const highlightedLlmResponse = highlightEntitiesInText(
        evaluation.llm_response,
        commonEntities
    );

    return `
        <div class="evaluation-item">
            <div class="evaluation-header collapsed" role="button" tabindex="0" aria-expanded="false" onclick="toggleEvaluation(this)">
                <div class="evaluation-id">Evaluation #${evaluation.input.id}</div>
                <div class="scores">
                    <div class="score-badge score-accuracy ${accuracyClass}">
                        Accuracy: ${(evaluation.accuracy.accuracy_mean * 100).toFixed(0)}%
                    </div>
                    <div class="score-badge score-coverage ${coverageClass}">
                        Coverage: ${(evaluation.topic_coverage.coverage_score * 100).toFixed(0)}%
                    </div>
                </div>
            </div>
            <div class="evaluation-content collapsed">

            <div class="query">
                <h3>Query</h3>
                <p>${evaluation.input.query}</p>
                <div class="context">
                    <strong>Context:</strong> ${convertLineBreaks(evaluation.input.context)}
                </div>
            </div>

            <div class="responses">
                <div class="response-card">
                    <div class="response-header expected-header">
                        Expected Answer
                    </div>
                    <div class="response-content">
                        ${highlightedExpectedAnswer}
                    </div>
                </div>
                <div class="response-card">
                    <div class="response-header llm-header">
                        LLM Response
                    </div>
                    <div class="response-content">
                        ${highlightedLlmResponse}
                    </div>
                </div>
            </div>

            <div class="reasoning">
                <h4>Expected Answer Reasoning</h4>
                ${formatReasoning(evaluation.input.reasoning)}
            </div>

            ${renderAxioms(evaluation.input.axioms_used)}

            ${renderEntities(evaluation.entities)}

            <div class="evaluation-scores">
                <h4>Evaluation Scores</h4>
                <div class="score-item">
                    <div class="score-header">
                        <h5>Accuracy (Mean)</h5>
                        <span class="score-badge ${accuracyClass}">
                            ${(evaluation.accuracy.accuracy_mean * 100).toFixed(0)}%
                        </span>
                    </div>
                    ${renderAccuracyDetails(evaluation.accuracy)}
                </div>
                <div class="score-item">
                    <div class="score-header">
                        <h5>Topic Coverage</h5>
                        <span class="score-badge ${coverageClass}">
                            ${(evaluation.topic_coverage.coverage_score * 100).toFixed(0)}%
                        </span>
                    </div>
                    <div class="score-reason">${convertLineBreaks(evaluation.topic_coverage.reason)}</div>
                </div>
            </div>
            </div>
        </div>
    `;
}

/**
 * Pre-processes all evaluation data to assign consistent colors to entities.
 * Ensures the same entity always gets the same color across all evaluations.
 * Collects all unique entities and assigns them sequential color indices.
 */
function initializeEntityColors() {
    // Pre-process all entities to assign consistent colors
    const allEntities = new Set();

    window.evaluationData.evaluation_outputs.forEach(evaluation => {
        const entities = evaluation.entities;

        // Collect all unique entities from the structure
        Object.values(entities).forEach(entityGroup => {
            if (Array.isArray(entityGroup)) {
                entityGroup.forEach(entity => {
                    if (entity.trigger_variable) {
                        allEntities.add(entity.trigger_variable);
                    }
                    if (entity.consequence_variable) {
                        allEntities.add(entity.consequence_variable);
                    }
                });
            }
        });
    });

    // Assign colors to all unique entities
    Array.from(allEntities).sort().forEach(entity => {
        getEntityColor(entity);
    });
}

/**
 * Calculates and displays summary statistics for all evaluations.
 * Computes average accuracy, coverage, and overall scores, then updates DOM elements.
 * Updates the summary statistics section at the top of the report.
 */
function calculateSummaryStats() {
    const evaluations = window.evaluationData.evaluation_outputs;
    const totalEvaluations = evaluations.length;

    const avgAccuracy = evaluations.reduce((sum, evaluation) => sum + evaluation.accuracy.accuracy_mean, 0) / totalEvaluations;
    const avgCoverage = evaluations.reduce((sum, evaluation) => sum + evaluation.topic_coverage.coverage_score, 0) / totalEvaluations;
    const overallScore = (avgAccuracy + avgCoverage) / 2;

    // Safely update summary statistics elements
    const totalEl = document.getElementById('total-evaluations');
    if (totalEl) totalEl.textContent = totalEvaluations;

    const accuracyEl = document.getElementById('avg-accuracy');
    if (accuracyEl) accuracyEl.textContent = avgAccuracy.toFixed(2);

    const coverageEl = document.getElementById('avg-coverage');
    if (coverageEl) coverageEl.textContent = avgCoverage.toFixed(2);

    const overallEl = document.getElementById('overall-score');
    if (overallEl) overallEl.textContent = overallScore.toFixed(2);
}

/**
 * Renders all evaluation items and inserts them into the DOM.
 * Processes each evaluation through renderEvaluation() and concatenates the results.
 * Updates the evaluations container with the complete HTML content.
 * Attaches keyboard event handlers to evaluation headers for accessibility.
 */
function renderEvaluations() {
    const container = document.getElementById('evaluations-container');
    if (!container) {
        console.error('Error: evaluations-container element not found');
        return;
    }

    const evaluationsHtml = window.evaluationData.evaluation_outputs
        .map(evaluation => renderEvaluation(evaluation))
        .join('');

    container.innerHTML = evaluationsHtml;

    // Attach keyboard event handlers for accessibility
    const headers = container.querySelectorAll('.evaluation-header');
    headers.forEach(header => {
        header.addEventListener('keydown', (event) => {
            // Trigger toggle on Enter or Space key
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault(); // Prevent page scroll on Space
                toggleEvaluation(header);
            }
        });
    });
}

/**
 * Toggles the collapsed/expanded state of an evaluation item.
 * Called when the evaluation header is clicked or activated via keyboard.
 * Manages CSS classes and ARIA attributes to control visibility and state
 * for both visual users and screen readers.
 * @param {HTMLElement} headerElement - The header element that was activated
 */
function toggleEvaluation(headerElement) {
    const content = headerElement.nextElementSibling;
    const isCollapsed = headerElement.classList.contains('collapsed');

    if (isCollapsed) {
        headerElement.classList.remove('collapsed');
        content.classList.remove('collapsed');
        headerElement.setAttribute('aria-expanded', 'true');
    } else {
        headerElement.classList.add('collapsed');
        content.classList.add('collapsed');
        headerElement.setAttribute('aria-expanded', 'false');
    }
}

/**
 * Main initialization function that loads evaluation data and sets up the page.
 * Fetches JSON data, validates structure, makes it globally available, and
 * initializes all page components.
 * Handles errors gracefully by displaying error messages to the user.
 */
// Load evaluation data and initialize the page
fetch('evaluation_data.json')
    .then(response => response.json())
    .then(evaluationData => {
        // Validate that evaluationData exists
        if (!evaluationData) {
            throw new Error('Evaluation data is null or undefined');
        }

        // Validate that evaluation_outputs exists and is an array
        if (!evaluationData.evaluation_outputs) {
            throw new Error('Missing required field: evaluation_outputs');
        }

        if (!Array.isArray(evaluationData.evaluation_outputs)) {
            throw new Error('evaluation_outputs must be an array, got: ' +
                typeof evaluationData.evaluation_outputs);
        }

        // Validate that evaluation_outputs is non-empty
        if (evaluationData.evaluation_outputs.length === 0) {
            throw new Error('evaluation_outputs array is empty - no evaluations to display');
        }

        // All validations passed - make evaluationData available globally
        window.evaluationData = evaluationData;

        // Initialize the page
        initializeEntityColors();
        calculateSummaryStats();
        renderEvaluations();
    })
    .catch(error => {
        console.error('Error loading evaluation data:', error);
        const container = document.getElementById('evaluations-container');
        if (container) {
            container.innerHTML =
                '<div style="padding: 20px; color: red;">' +
                '<strong>Error loading evaluation data:</strong><br>' +
                error.message +
                '<br><br>Please check the console for more details.</div>';
        }
    });
