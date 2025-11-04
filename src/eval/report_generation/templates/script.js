// Global entity color mapping
const entityColorMap = new Map();
let colorIndex = 0;

function getEntityColor(entity) {
    if (!entityColorMap.has(entity)) {
        entityColorMap.set(entity, colorIndex % 20);
        colorIndex++;
    }
    return entityColorMap.get(entity);
}

function getScoreClass(score) {
    if (score >= 0.7) return 'score-good';
    if (score >= 0.4) return 'score-medium';
    return 'score-poor';
}

function convertLineBreaks(text) {
    if (!text) return text;
    return text
        .replace(/\r\n/g, '<br>')
        .replace(/\n/g, '<br>')
        .replace(/\r/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
}

function formatReasoning(reasoning) {
    if (Array.isArray(reasoning)) {
        return '<ul>' + reasoning.map(item =>
            `<li>${convertLineBreaks(item)}</li>`).join('') + '</ul>';
    }
    return convertLineBreaks(reasoning);
}

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
            <div class="evaluation-header collapsed" onclick="toggleEvaluation(this)">
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

function initializeEntityColors() {
    // Pre-process all entities to assign consistent colors
    const allEntities = new Set();

    evaluationData.evaluation_outputs.forEach(evaluation => {
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

function calculateSummaryStats() {
    const evaluations = evaluationData.evaluation_outputs;
    const totalEvaluations = evaluations.length;

    const avgAccuracy = evaluations.reduce((sum, evaluation) => sum + evaluation.accuracy.accuracy_mean, 0) / totalEvaluations;
    const avgCoverage = evaluations.reduce((sum, evaluation) => sum + evaluation.topic_coverage.coverage_score, 0) / totalEvaluations;
    const overallScore = (avgAccuracy + avgCoverage) / 2;

    document.getElementById('total-evaluations').textContent = totalEvaluations;
    document.getElementById('avg-accuracy').textContent = avgAccuracy.toFixed(2);
    document.getElementById('avg-coverage').textContent = avgCoverage.toFixed(2);
    document.getElementById('overall-score').textContent = overallScore.toFixed(2);
}

function renderEvaluations() {
    const container = document.getElementById('evaluations-container');
    const evaluationsHtml = evaluationData.evaluation_outputs
        .map(evaluation => renderEvaluation(evaluation))
        .join('');

    container.innerHTML = evaluationsHtml;
}

function toggleEvaluation(headerElement) {
    const content = headerElement.nextElementSibling;
    const isCollapsed = headerElement.classList.contains('collapsed');

    if (isCollapsed) {
        headerElement.classList.remove('collapsed');
        content.classList.remove('collapsed');
    } else {
        headerElement.classList.add('collapsed');
        content.classList.add('collapsed');
    }
}

// Load evaluation data and initialize the page
fetch('evaluation_data.json')
    .then(response => response.json())
    .then(evaluationData => {
        // Make evaluationData available globally
        window.evaluationData = evaluationData;

        // Initialize the page
        initializeEntityColors();
        calculateSummaryStats();
        renderEvaluations();
    })
    .catch(error => {
        console.error('Error loading evaluation data:', error);
        document.getElementById('evaluations-container').innerHTML =
            '<div style="padding: 20px; color: red;">Error loading evaluation data. Please check the console.</div>';
    });
