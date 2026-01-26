// ============================================================================
// Type Definitions (JSDoc)
// ============================================================================

/**
 * @typedef {Object} EntityPair
 * @property {string} trigger_variable - The trigger variable name
 * @property {string} consequence_variable - The consequence variable name
 */

/**
 * @typedef {Object} Entities
 * @property {EntityPair[]} user_query_entities - Entities from user query
 * @property {EntityPair[]} expected_answer_entities - Entities from expected answer
 * @property {EntityPair[]} llm_answer_entities - Entities from LLM response
 */

/**
 * @typedef {Object} ReferenceResults
 * @property {string[]} references_expected - Expected reference identifiers
 * @property {string[]} references_found - Found reference identifiers in response
 * @property {number} precision - Precision score (0-1)
 * @property {number} recall - Recall score (0-1)
 */

/**
 * @typedef {Object} EntityAccuracyResult
 * @property {EntityPair} entity - The entity pair being evaluated
 * @property {number} score - Accuracy score (0-1)
 * @property {string} reason - Explanation for the score
 */

/**
 * @typedef {Object} AccuracyResults
 * @property {number} accuracy_mean - Mean accuracy across all entities
 * @property {EntityAccuracyResult[]} entity_accuracies - Per-entity accuracy results
 */

/**
 * @typedef {Object} TopicCoverage
 * @property {number} coverage_score - Coverage score (0-1)
 * @property {string} reason - Explanation for the score
 */

/**
 * @typedef {Object} EvaluationInput
 * @property {number} id - Evaluation identifier
 * @property {string} query - The user query
 * @property {string} context - Context provided for the query
 * @property {string} expected_answer - Expected correct answer
 * @property {string|string[]} reasoning - Reasoning for expected answer
 */

/**
 * @typedef {Object} EvaluationOutput
 * @property {EvaluationInput} input - The input data for this evaluation
 * @property {string} llm_response - The LLM's generated response
 * @property {Entities} entities - Identified entities
 * @property {AccuracyResults} accuracy - Accuracy evaluation results
 * @property {TopicCoverage} topic_coverage - Topic coverage results
 * @property {ReferenceResults} [axiom_references] - Axiom reference results (optional)
 * @property {ReferenceResults} [reality_references] - Reality reference results (optional)
 */

/**
 * @typedef {Object} MetricSummary
 * @property {number} mean - Mean value of the metric
 * @property {number} [min] - Minimum value (optional)
 * @property {number} [max] - Maximum value (optional)
 */

/**
 * @typedef {Object} EvaluationData
 * @property {EvaluationOutput[]} evaluation_outputs - Array of evaluation results
 * @property {MetricSummary} [accuracy] - Accuracy metric summary
 * @property {MetricSummary} [topic_coverage] - Topic coverage metric summary
 * @property {MetricSummary} [axiom_precision_metric] - Axiom precision metric summary
 * @property {MetricSummary} [axiom_recall_metric] - Axiom recall metric summary
 * @property {MetricSummary} [reality_precision_metric] - Reality precision metric summary
 * @property {MetricSummary} [reality_recall_metric] - Reality recall metric summary
 * @property {AxiomItem[]} [axiom_definitions] - Axiom definitions (optional)
 * @property {RealityItem[]} [reality_definitions] - Reality item definitions (optional)
 */

/**
 * @typedef {Object} AxiomItem
 * @property {string} id - Unique identifier for the axiom
 * @property {string} description - Description of the axiom
 */

/**
 * @typedef {Object} RealityItem
 * @property {string} id - Unique identifier for the reality item
 * @property {string} description - Description of the reality item
 */

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Escapes HTML special characters to prevent XSS attacks.
 * @param {string} unsafe - String that may contain HTML special characters
 * @returns {string} Escaped string safe for HTML insertion
 */
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') {
        return '';
    }
    return unsafe
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ============================================================================
// Global State
// ============================================================================

/** @type {Map<string, number>} Maps entity names to their assigned color index */
const entityColorMap = new Map();

/** @type {number} Counter for assigning sequential color indices */
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
 * Creates an HTML score badge with appropriate color styling.
 * @param {string} label - The label to display (e.g., "Accuracy", "Coverage")
 * @param {number} score - The score value between 0 and 1
 * @param {string} [extraClass] - Optional additional CSS class (e.g., "score-accuracy")
 * @returns {string} HTML string for the score badge
 */
function createScoreBadge(label, score, extraClass = '') {
    const scoreClass = getScoreClass(score);
    const classes = extraClass ? `score-badge ${extraClass} ${scoreClass}` : `score-badge ${scoreClass}`;
    return `<div class="${classes}">${label}: ${(score * 100).toFixed(0)}%</div>`;
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
 * Builds a lookup map from definitions array for quick ID-to-description lookup.
 * Works with both axiom definitions (axiom_id) and reality definitions (reality_id).
 * @param {AxiomItem[]|RealityItem[]|undefined} definitions - Array of definition items
 * @returns {Map<string, string>} Map from ID to description
 */
function buildDefinitionsMap(definitions) {
    const map = new Map();
    if (!definitions || !Array.isArray(definitions)) {
        return map;
    }
    definitions.forEach(item => {
        // Both axiom and reality items use 'id' field
        const id = item.id;
        if (id && item.description) {
            map.set(id, item.description);
        }
    });
    return map;
}

/**
 * Renders a single reference tag with optional tooltip showing description.
 * @param {string} refId - The reference ID (e.g., "A-001" or "R-001")
 * @param {string} tagClass - CSS class for the tag styling
 * @param {Map<string, string>} definitionsMap - Map from ID to description
 * @returns {string} HTML string for the reference tag
 */
function renderReferenceTag(refId, tagClass, definitionsMap) {
    const escapedRefId = escapeHtml(refId);
    const description = definitionsMap.get(refId);
    if (description) {
        // Escape description for safe attribute value (already done by escapeHtml)
        const escapedDescription = escapeHtml(description);
        return `<span class="reference-tag ${tagClass}" data-tooltip="${escapedDescription}" tabindex="0">${escapedRefId}</span>`;
    }
    return `<span class="reference-tag ${tagClass}">${escapedRefId}</span>`;
}

/**
 * Renders a comparison of expected vs found references (axioms or realities).
 * Shows precision and recall scores along with the lists of references.
 * Reference tags display tooltips with descriptions when definitions are provided.
 * @param {string} title - The title for the section (e.g., "Axiom References")
 * @param {ReferenceResults|null|undefined} references - Reference evaluation results
 * @param {Map<string, string>} [definitionsMap] - Optional map from ID to description for tooltips
 * @returns {string} HTML string containing the references comparison section, or empty string if no references
 */
function renderReferences(title, references, definitionsMap) {
    if (!references) {
        return '';
    }

    const defMap = definitionsMap || new Map();
    const precisionClass = getScoreClass(references.precision);
    const recallClass = getScoreClass(references.recall);

    return `
        <div class="references-section">
            <h4>${title}</h4>
            <div class="references-grid">
                <div class="references-card">
                    <h5>Expected</h5>
                    <div class="reference-list">
                        ${references.references_expected.length > 0 ?
            references.references_expected.map(ref =>
                renderReferenceTag(ref, 'expected-tag', defMap)
            ).join('') :
            '<p style="color: #666; font-style: italic;">None expected</p>'}
                    </div>
                </div>
                <div class="references-card">
                    <h5>Found in Response</h5>
                    <div class="reference-list">
                        ${references.references_found.length > 0 ?
            references.references_found.map(ref => {
                const isMatch = references.references_expected.includes(ref);
                const tagClass = isMatch ? 'found-match-tag' : 'found-nomatch-tag';
                return renderReferenceTag(ref, tagClass, defMap);
            }).join('') :
            '<p style="color: #666; font-style: italic;">None found</p>'}
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

/**
 * Renders entity information in a three-column grid layout.
 * Displays query entities, expected answer entities, and LLM answer entities.
 * Each entity pair shows trigger variable → consequence variable with consistent colors.
 * @param {Entities} entities - Object containing three arrays of entity pairs
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
 * @param {AccuracyResults} accuracy - Accuracy evaluation results
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
                            <span class="entity-tag entity-color-${getEntityColor(result.entity.trigger_variable)}">${result.entity.trigger_variable}</span>
                            <span style="color: #666; margin: 0 5px;">→</span>
                            <span class="entity-tag entity-color-${getEntityColor(result.entity.consequence_variable)}">${result.entity.consequence_variable}</span>
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
 * @param {EvaluationOutput} evaluation - Complete evaluation object containing input, responses, and scores
 * @param {Map<string, string>} axiomDefinitionsMap - Map from axiom ID to description
 * @param {Map<string, string>} realityDefinitionsMap - Map from reality ID to description
 * @returns {string} HTML string containing the full evaluation display
 */
function renderEvaluation(evaluation, axiomDefinitionsMap, realityDefinitionsMap) {
    const accuracyScore = evaluation.accuracy.accuracy_mean;
    const coverageScore = evaluation.topic_coverage.coverage_score;
    const axiomPrecisionScore = evaluation.axiom_references?.precision ?? 0;
    const axiomRecallScore = evaluation.axiom_references?.recall ?? 0;
    const realityPrecisionScore = evaluation.reality_references?.precision ?? 0;
    const realityRecallScore = evaluation.reality_references?.recall ?? 0;

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
                    ${createScoreBadge('Accuracy', accuracyScore, 'score-accuracy')}
                    ${createScoreBadge('Coverage', coverageScore, 'score-coverage')}
                    ${createScoreBadge('Axiom P', axiomPrecisionScore)}
                    ${createScoreBadge('Axiom R', axiomRecallScore)}
                    ${createScoreBadge('Reality P', realityPrecisionScore)}
                    ${createScoreBadge('Reality R', realityRecallScore)}
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

            ${renderReferences('Axiom References', evaluation.axiom_references, axiomDefinitionsMap)}
            ${renderReferences('Reality References', evaluation.reality_references, realityDefinitionsMap)}

            ${renderEntities(evaluation.entities)}

            <div class="evaluation-scores">
                <h4>Evaluation Scores</h4>
                <div class="score-item">
                    <div class="score-header">
                        <h5>Accuracy (Mean)</h5>
                        <span class="score-badge ${getScoreClass(accuracyScore)}">
                            ${(accuracyScore * 100).toFixed(0)}%
                        </span>
                    </div>
                    ${renderAccuracyDetails(evaluation.accuracy)}
                </div>
                <div class="score-item">
                    <div class="score-header">
                        <h5>Topic Coverage</h5>
                        <span class="score-badge ${getScoreClass(coverageScore)}">
                            ${(coverageScore * 100).toFixed(0)}%
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
 * @returns {void}
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
 * Displays summary statistics from pre-calculated metrics in the evaluation data.
 * Updates the summary statistics section at the top of the report.
 * Includes defensive checks for missing metric fields.
 * @returns {void}
 */
function calculateSummaryStats() {
    const data = window.evaluationData;
    const totalEvaluations = data.evaluation_outputs?.length ?? 0;

    // Use pre-calculated metrics from the JSON with defensive null checks
    const avgAccuracy = data.accuracy?.mean ?? 0;
    const avgCoverage = data.topic_coverage?.mean ?? 0;
    const avgAxiomPrecision = data.axiom_precision_metric?.mean ?? 0;
    const avgAxiomRecall = data.axiom_recall_metric?.mean ?? 0;
    const avgRealityPrecision = data.reality_precision_metric?.mean ?? 0;
    const avgRealityRecall = data.reality_recall_metric?.mean ?? 0;

    // Overall score is the unweighted average of all 6 evaluation metrics:
    // - Accuracy: How well the LLM response matches the expected answer
    // - Coverage: How well the response covers the expected topics
    // - Axiom Precision: Proportion of cited axioms that are relevant
    // - Axiom Recall: Proportion of relevant axioms that were cited
    // - Reality Precision: Proportion of cited reality facts that are relevant
    // - Reality Recall: Proportion of relevant reality facts that were cited
    const overallScore = (
        avgAccuracy +
        avgCoverage +
        avgAxiomPrecision +
        avgAxiomRecall +
        avgRealityPrecision +
        avgRealityRecall
    ) / 6;

    // Safely update summary statistics elements
    const totalEl = document.getElementById('total-evaluations');
    if (totalEl) totalEl.textContent = totalEvaluations;

    const accuracyEl = document.getElementById('avg-accuracy');
    if (accuracyEl) accuracyEl.textContent = avgAccuracy.toFixed(2);

    const coverageEl = document.getElementById('avg-coverage');
    if (coverageEl) coverageEl.textContent = avgCoverage.toFixed(2);

    const axiomPrecisionEl = document.getElementById('avg-axiom-precision');
    if (axiomPrecisionEl) axiomPrecisionEl.textContent = avgAxiomPrecision.toFixed(2);

    const axiomRecallEl = document.getElementById('avg-axiom-recall');
    if (axiomRecallEl) axiomRecallEl.textContent = avgAxiomRecall.toFixed(2);

    const realityPrecisionEl = document.getElementById('avg-reality-precision');
    if (realityPrecisionEl) realityPrecisionEl.textContent = avgRealityPrecision.toFixed(2);

    const realityRecallEl = document.getElementById('avg-reality-recall');
    if (realityRecallEl) realityRecallEl.textContent = avgRealityRecall.toFixed(2);

    const overallEl = document.getElementById('overall-score');
    if (overallEl) overallEl.textContent = overallScore.toFixed(2);
}

/**
 * Renders all evaluation items and inserts them into the DOM.
 * Processes each evaluation through renderEvaluation() and concatenates the results.
 * Updates the evaluations container with the complete HTML content.
 * Attaches keyboard event handlers to evaluation headers for accessibility.
 * @returns {void}
 */
function renderEvaluations() {
    const container = document.getElementById('evaluations-container');
    if (!container) {
        console.error('Error: evaluations-container element not found');
        return;
    }

    // Build definitions lookup maps for tooltips
    const axiomDefinitionsMap = buildDefinitionsMap(window.evaluationData.axiom_definitions);
    const realityDefinitionsMap = buildDefinitionsMap(window.evaluationData.reality_definitions);

    const evaluationsHtml = window.evaluationData.evaluation_outputs
        .map(evaluation => renderEvaluation(evaluation, axiomDefinitionsMap, realityDefinitionsMap))
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
 * Toggles the collapsed/expanded state of a definitions section.
 * Called when the definitions header is clicked or activated via keyboard.
 * Manages CSS classes and ARIA attributes to control visibility and state.
 * @param {HTMLElement} headerElement - The header element that was activated
 */
function toggleDefinitionsSection(headerElement) {
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
 * Attaches keyboard event handlers to definitions headers for accessibility.
 * Enables Enter and Space key to toggle collapsed state.
 * @returns {void}
 */
function setupDefinitionsKeyboardHandlers() {
    const headers = document.querySelectorAll('.definitions-header');
    headers.forEach(header => {
        header.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                toggleDefinitionsSection(header);
            }
        });
    });
}

// ============================================================================
// Definition Rendering
// ============================================================================

/**
 * Renders the axiom definitions section.
 * Populates the axiom-definitions-list element with definition items.
 * Shows a message if no definitions are available.
 * @returns {void}
 */
function renderAxiomDefinitions() {
    const container = document.getElementById('axiom-definitions-list');
    if (!container) {
        console.error('Error: axiom-definitions-list element not found');
        return;
    }

    const definitions = window.evaluationData.axiom_definitions;
    if (!definitions || definitions.length === 0) {
        container.innerHTML =
            '<p class="no-definitions">No axiom definitions available.</p>';
        return;
    }

    const definitionsHtml = definitions
        .map(item => `
            <div class="definition-item">
                <span class="definition-id">${escapeHtml(item.id)}</span>
                <span class="definition-text">${escapeHtml(item.description)}</span>
            </div>
        `)
        .join('');

    container.innerHTML = definitionsHtml;
}

/**
 * Renders the reality item definitions section.
 * Populates the reality-definitions-list element with definition items.
 * Shows a message if no definitions are available.
 * @returns {void}
 */
function renderRealityDefinitions() {
    const container = document.getElementById('reality-definitions-list');
    if (!container) {
        console.error('Error: reality-definitions-list element not found');
        return;
    }

    const definitions = window.evaluationData.reality_definitions;
    if (!definitions || definitions.length === 0) {
        container.innerHTML =
            '<p class="no-definitions">No reality definitions available.</p>';
        return;
    }

    // Clear any existing content before rendering definitions
    container.innerHTML = '';

    definitions.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'definition-item';

        const idSpan = document.createElement('span');
        idSpan.className = 'definition-id';
        idSpan.textContent = item.id;

        const textSpan = document.createElement('span');
        textSpan.className = 'definition-text';
        textSpan.textContent = item.description;

        itemDiv.appendChild(idSpan);
        itemDiv.appendChild(textSpan);

        container.appendChild(itemDiv);
    });
}

// ============================================================================
// Initialization
// ============================================================================

/**
 * Main initialization - loads evaluation data and sets up the page.
 * Fetches JSON data, validates structure, makes it globally available, and
 * initializes all page components.
 * Handles errors gracefully by displaying error messages to the user.
 */
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
        renderAxiomDefinitions();
        renderRealityDefinitions();
        setupDefinitionsKeyboardHandlers();
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
