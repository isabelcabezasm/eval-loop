"""Report generation main script."""

import argparse
import json
import os
from pathlib import Path
from typing import Any


class Report:
    """Handles generation of HTML evaluation reports from JSON data."""

    def __init__(self, data_path: str, output_dir: str | None = None):
        """Initialize the Report instance.

        Args:
            data_path: Path to the evaluation data JSON file
            output_dir: Output directory for generated files (optional)
        """
        self.data_path = data_path
        self.output_dir = output_dir
        self.evaluation_data: dict[str, Any] = {}

    def load_json_data(self) -> dict[str, Any]:
        """Load evaluation data from JSON file."""
        with open(self.data_path, encoding="utf-8") as file:
            self.evaluation_data = json.load(file)
            return self.evaluation_data

    def generate_css(self) -> str:
        """Generate CSS content for the HTML report."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .summary {
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }

        .summary-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .summary-card h3 {
            font-size: 2rem;
            color: #667eea;
            margin-bottom: 5px;
        }

        .summary-card p {
            color: #666;
            font-size: 0.9rem;
        }

        .evaluation-item {
            border-bottom: 1px solid #e9ecef;
        }

        .evaluation-item:last-child {
            border-bottom: none;
        }

        .evaluation-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 20px 30px;
            flex-wrap: wrap;
            gap: 15px;
            cursor: pointer;
            transition: background-color 0.2s ease;
            position: relative;
        }

        .evaluation-header:hover {
            background-color: #f8f9fa;
        }

        .evaluation-header::after {
            content: '▼';
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            transition: transform 0.3s ease;
            font-size: 0.8rem;
            color: #666;
        }

        .evaluation-header.collapsed::after {
            transform: translateY(-50%) rotate(-90deg);
        }

        .evaluation-content {
            padding: 0 30px 30px 30px;
            display: block;
        }

        .evaluation-content.collapsed {
            display: none;
        }

        .evaluation-id {
            background: #667eea;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
        }

        .scores {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .score-badge {
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
            text-align: center;
            min-width: 80px;
        }

        .score-accuracy {
            background: #ff6b6b;
            color: white;
        }

        .score-coverage {
            background: #4ecdc4;
            color: white;
        }

        .score-good {
            background: #51cf66;
        }

        .score-medium {
            background: #ffd43b;
        }

        .score-poor {
            background: #ff6b6b;
        }

        .query {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }

        .query h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1rem;
        }

        .query p {
            font-size: 1rem;
            line-height: 1.5;
        }

        .context {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #2196f3;
            font-size: 0.9rem;
            line-height: 1.5;
        }

        .responses {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }

        @media (max-width: 768px) {
            .responses {
                grid-template-columns: 1fr;
            }

            .evaluation-header {
                flex-direction: column;
                align-items: stretch;
            }

            .scores {
                justify-content: center;
            }
        }

        .response-card {
            border: 1px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
        }

        .response-header {
            padding: 15px;
            font-weight: bold;
            color: white;
        }

        .expected-header {
            background: #28a745;
        }

        .llm-header {
            background: #dc3545;
        }

        .response-content {
            padding: 15px;
            background: white;
        }

        .reasoning {
            background: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #ffc107;
        }

        .reasoning h4 {
            color: #856404;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }

        .reasoning p,
        .reasoning ul {
            font-size: 0.9rem;
            line-height: 1.4;
        }

        .reasoning ul {
            padding-left: 20px;
            margin-top: 8px;
        }

        .axioms {
            margin: 20px 0;
            background: #e8f5e8;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }

        .axioms h4 {
            color: #28a745;
            margin-bottom: 10px;
            font-size: 1rem;
        }

        .axiom-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .axiom-tag {
            background: #28a745;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        .entities {
            margin: 20px 0;
        }

        .entities h4 {
            margin-bottom: 15px;
            color: #495057;
        }

        .entity-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }

        .entity-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }

        .entity-card h5 {
            color: #495057;
            margin-bottom: 10px;
            font-size: 0.9rem;
        }

        .entity-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .entity-pair {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 5px;
        }

        .entity-tag {
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        /* Entity color classes - consistent colors for same entities across sections */
        .entity-color-0 { background-color: #667eea; }
        .entity-color-1 { background-color: #f093fb; }
        .entity-color-2 { background-color: #4ecdc4; }
        .entity-color-3 { background-color: #45b7d1; }
        .entity-color-4 { background-color: #96ceb4; }
        .entity-color-5 { background-color: #ffecd2; color: #333; }
        .entity-color-6 { background-color: #a8edea; color: #333; }
        .entity-color-7 { background-color: #d299c2; }
        .entity-color-8 { background-color: #fad0c4; color: #333; }
        .entity-color-9 { background-color: #a18cd1; }
        .entity-color-10 { background-color: #fbc2eb; color: #333; }
        .entity-color-11 { background-color: #84fab0; color: #333; }
        .entity-color-12 { background-color: #f6d365; color: #333; }
        .entity-color-13 { background-color: #fa709a; }
        .entity-color-14 { background-color: #fee140; color: #333; }
        .entity-color-15 { background-color: #a8edea; color: #333; }
        .entity-color-16 { background-color: #d0bfff; color: #333; }
        .entity-color-17 { background-color: #b8f2ff; color: #333; }
        .entity-color-18 { background-color: #ffd93d; color: #333; }
        .entity-color-19 { background-color: #74c0fc; color: #333; }

        /* Entity highlighting in text - same colors but with transparency */
        .entity-highlight {
            padding: 2px 4px;
            border-radius: 4px;
            font-weight: 500;
        }

        .entity-highlight.entity-color-0 { background-color: rgba(102, 126, 234, 0.3); }
        .entity-highlight.entity-color-1 { background-color: rgba(240, 147, 251, 0.3); }
        .entity-highlight.entity-color-2 { background-color: rgba(78, 205, 196, 0.3); }
        .entity-highlight.entity-color-3 { background-color: rgba(69, 183, 209, 0.3); }
        .entity-highlight.entity-color-4 { background-color: rgba(150, 206, 180, 0.3); }
        .entity-highlight.entity-color-5 { 
            background-color: rgba(255, 236, 210, 0.5); 
        }
        .entity-highlight.entity-color-6 { 
            background-color: rgba(168, 237, 234, 0.5); 
        }
        .entity-highlight.entity-color-7 { background-color: rgba(210, 153, 194, 0.3); }
        .entity-highlight.entity-color-8 { 
            background-color: rgba(250, 208, 196, 0.5); 
        }
        .entity-highlight.entity-color-9 { background-color: rgba(161, 140, 209, 0.3); }
        .entity-highlight.entity-color-10 { 
            background-color: rgba(251, 194, 235, 0.5); 
        }
        .entity-highlight.entity-color-11 { 
            background-color: rgba(132, 250, 176, 0.5); 
        }
        .entity-highlight.entity-color-12 { 
            background-color: rgba(246, 211, 101, 0.5); 
        }
        .entity-highlight.entity-color-13 { background-color: rgba(250, 112, 154, 0.3); }
        .entity-highlight.entity-color-14 { 
            background-color: rgba(254, 225, 64, 0.5); 
        }
        .entity-highlight.entity-color-15 { 
            background-color: rgba(168, 237, 234, 0.5); 
        }
        .entity-highlight.entity-color-16 { 
            background-color: rgba(208, 191, 255, 0.5); 
        }
        .entity-highlight.entity-color-17 { 
            background-color: rgba(184, 242, 255, 0.5); 
        }
        .entity-highlight.entity-color-18 { 
            background-color: rgba(255, 217, 61, 0.5); 
        }
        .entity-highlight.entity-color-19 { 
            background-color: rgba(116, 192, 252, 0.5); 
        }

        .evaluation-scores {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }

        .evaluation-scores h4 {
            margin-bottom: 15px;
            color: #495057;
        }

        .score-item {
            margin-bottom: 15px;
            padding: 15px;
            background: white;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }

        .score-item:last-child {
            margin-bottom: 0;
        }

        .score-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .score-header h5 {
            color: #495057;
            font-size: 1rem;
        }

        .score-reason {
            color: #666;
            font-size: 0.9rem;
            line-height: 1.4;
        }

        .accuracy-details {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }

        .accuracy-details h5 {
            color: #495057;
            margin-bottom: 10px;
            font-size: 0.9rem;
        }

        .accuracy-result {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 10px;
            background: white;
            border-radius: 6px;
            margin-bottom: 10px;
            border-left: 3px solid #28a745;
        }

        .accuracy-result:last-child {
            margin-bottom: 0;
        }

        .accuracy-entity {
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }

        .accuracy-reason {
            font-size: 0.85rem;
            color: #666;
            line-height: 1.3;
        }

        .accuracy-score {
            font-weight: bold;
            color: #28a745;
            font-size: 0.9rem;
        }
        """

    def generate_javascript(self) -> str:
        """Generate JavaScript content with embedded evaluation data."""
        json_data = json.dumps(self.evaluation_data, indent=8)

        return f"""        
        // Global entity color mapping
        const entityColorMap = new Map();
        let colorIndex = 0;

        function getEntityColor(entity) {{
            if (!entityColorMap.has(entity)) {{
                entityColorMap.set(entity, colorIndex % 20);
                colorIndex++;
            }}
            return entityColorMap.get(entity);
        }}

        function getScoreClass(score) {{
            if (score >= 0.7) return 'score-good';
            if (score >= 0.4) return 'score-medium';
            return 'score-poor';
        }}

        function convertLineBreaks(text) {{
            if (!text) return text;
            return text
                .replace(/\\r\\n/g, '<br>')
                .replace(/\\n/g, '<br>')
                .replace(/\\r/g, '<br>')
                .replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>');
        }}

        function formatReasoning(reasoning) {{
            if (Array.isArray(reasoning)) {{
                return '<ul>' + reasoning.map(item => 
                    `<li>${{convertLineBreaks(item)}}</li>`).join('') + '</ul>';
            }}
            return convertLineBreaks(reasoning);
        }}

        function findEntitiesInText(text, entities) {{
            if (!text || !entities || entities.length === 0) {{
                return [];
            }}

            const foundEntities = [];
            entities.forEach(entity => {{
                // Create a case-insensitive regex that matches whole words
                const regex = new RegExp(
                    `\\\\b${{entity.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&')}}\\\\b`, 
                    'gi'
                );
                if (regex.test(text)) {{
                    foundEntities.push(entity);
                }}
            }});

            return foundEntities;
        }}

        function highlightEntitiesInText(text, entities) {{
            if (!text || !entities || entities.length === 0) {{
                return convertLineBreaks(text);
            }}

            let highlightedText = text;

            // Sort entities by length (longest first) to avoid partial matches
            const sortedEntities = [...entities].sort((a, b) => b.length - a.length);

            sortedEntities.forEach(entity => {{
                const colorClass = `entity-color-${{getEntityColor(entity)}}`;
                // Create a case-insensitive regex that matches whole words
                const regex = new RegExp(
                    `\\\\b${{entity.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&')}}\\\\b`, 
                    'gi'
                );
                highlightedText = highlightedText.replace(
                    regex, 
                    `<span class="entity-highlight ${{colorClass}}">${{entity}}</span>`
                );
            }});

            return convertLineBreaks(highlightedText);
        }}

        function renderAxioms(axioms) {{
            if (!axioms || axioms.length === 0) {{
                return '';
            }}

            return `
                <div class="axioms">
                    <h4>Related Axioms</h4>
                    <div class="axiom-list">
                        ${{axioms.map(axiom => `
                            <span class="axiom-tag">${{axiom}}</span>
                        `).join('')}}
                    </div>
                </div>
            `;
        }}

        function renderEntities(entities) {{
            return `
                <div class="entities">
                    <h4>Identified Entities</h4>
                    <div class="entity-grid">
                        <div class="entity-card">
                            <h5>Query Entities</h5>
                            <div class="entity-list">
                                ${{entities.user_query_entities.length > 0 ? 
                                entities.user_query_entities.map(entity => `
                                    <div class="entity-pair">
                                        <span class="entity-tag entity-color-${{
                                            getEntityColor(entity.trigger_variable)
                                        }}">${{entity.trigger_variable}}</span>
                                        <span style="color: #666; margin: 0 5px;">
                                            →
                                        </span>
                                        <span class="entity-tag entity-color-${{
                                            getEntityColor(entity.consequence_variable)
                                        }}">${{entity.consequence_variable}}</span>
                                    </div>
                                `).join('') : 
                                '<p style="color: #666; font-style: italic;">' +
                                'No entities identified</p>'}}
                            </div>
                        </div>
                        <div class="entity-card">
                            <h5>Expected Answer Entities</h5>
                            <div class="entity-list">
                                ${{entities.expected_answer_entities.length > 0 ? 
                                entities.expected_answer_entities.map(entity => `
                                    <div class="entity-pair">
                                        <span class="entity-tag entity-color-${{
                                            getEntityColor(entity.trigger_variable)
                                        }}">${{entity.trigger_variable}}</span>
                                        <span style="color: #666; margin: 0 5px;">
                                            →
                                        </span>
                                        <span class="entity-tag entity-color-${{
                                            getEntityColor(entity.consequence_variable)
                                        }}">${{entity.consequence_variable}}</span>
                                    </div>
                                `).join('') : 
                                '<p style="color: #666; font-style: italic;">' +
                                'No entities identified</p>'}}
                            </div>
                        </div>
                        <div class="entity-card">
                            <h5>LLM Answer Entities</h5>
                            <div class="entity-list">
                                ${{entities.llm_answer_entities.length > 0 ? 
                                entities.llm_answer_entities.map(entity => `
                                    <div class="entity-pair">
                                        <span class="entity-tag entity-color-${{
                                            getEntityColor(entity.trigger_variable)
                                        }}">${{entity.trigger_variable}}</span>
                                        <span style="color: #666; margin: 0 5px;">
                                            →
                                        </span>
                                        <span class="entity-tag entity-color-${{
                                            getEntityColor(entity.consequence_variable)
                                        }}">${{entity.consequence_variable}}</span>
                                    </div>
                                `).join('') : 
                                '<p style="color: #666; font-style: italic;">' +
                                'No entities identified</p>'}}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }}

        function renderAccuracyDetails(accuracy) {{
            return `
                <div class="accuracy-details">
                    <h5>Entity-Level Accuracy</h5>
                    ${{accuracy.entity_accuracies.map(result => `
                        <div class="accuracy-result">
                            <div>
                                <div class="accuracy-entity">
                                    ${{result.entity}}
                                </div>
                                <div class="accuracy-reason">
                                    ${{convertLineBreaks(result.reason)}}
                                </div>
                            </div>
                            <div class="accuracy-score">
                                ${{(result.score * 100).toFixed(0)}}%
                            </div>
                        </div>
                    `).join('')}}
                </div>
            `;
        }}

        function renderEvaluation(evaluation) {{
            const accuracyClass = getScoreClass(evaluation.accuracy.accuracy_mean);
            const coverageClass = getScoreClass(
                evaluation.topic_coverage.coverage_score
            );

            // Collect all entities for analysis
            const allEntityValues = [];

            // Extract trigger and consequence variables from all entity objects
            [evaluation.entities.user_query_entities,
            evaluation.entities.llm_answer_entities,
            evaluation.entities.expected_answer_entities].forEach(entityList => {{
                if (Array.isArray(entityList)) {{
                    entityList.forEach(entity => {{
                        if (entity.trigger_variable) {{
                            allEntityValues.push(entity.trigger_variable);
                        }}
                        if (entity.consequence_variable) {{
                            allEntityValues.push(entity.consequence_variable);
                        }}
                    }});
                }}
            }});

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
                        <div class="evaluation-id">Evaluation #${{evaluation.input.id}}</div>
                        <div class="scores">
                            <div class="score-badge score-accuracy ${{accuracyClass}}">
                                Accuracy: ${{(evaluation.accuracy.accuracy_mean * 100).toFixed(0)}}%
                            </div>
                            <div class="score-badge score-coverage ${{coverageClass}}">
                                Coverage: ${{(evaluation.topic_coverage.coverage_score * 100).toFixed(0)}}%
                            </div>
                        </div>
                    </div>
                    <div class="evaluation-content collapsed">

                    <div class="query">
                        <h3>Query</h3>
                        <p>${{evaluation.input.query}}</p>
                        <div class="context">
                            <strong>Context:</strong> ${{convertLineBreaks(evaluation.input.context)}}
                        </div>
                    </div>

                    <div class="responses">
                        <div class="response-card">
                            <div class="response-header expected-header">
                                Expected Answer
                            </div>
                            <div class="response-content">
                                ${{highlightedExpectedAnswer}}
                            </div>
                        </div>
                        <div class="response-card">
                            <div class="response-header llm-header">
                                LLM Response
                            </div>
                            <div class="response-content">
                                ${{highlightedLlmResponse}}
                            </div>
                        </div>
                    </div>

                    <div class="reasoning">
                        <h4>Expected Answer Reasoning</h4>
                        ${{formatReasoning(evaluation.input.reasoning)}}
                    </div>

                    ${{renderAxioms(evaluation.input.axioms_used)}}

                    ${{renderEntities(evaluation.entities)}}

                    <div class="evaluation-scores">
                        <h4>Evaluation Scores</h4>
                        <div class="score-item">
                            <div class="score-header">
                                <h5>Accuracy (Mean)</h5>
                                <span class="score-badge ${{accuracyClass}}">
                                    ${{(evaluation.accuracy.accuracy_mean * 100).toFixed(0)}}%
                                </span>
                            </div>
                            ${{renderAccuracyDetails(evaluation.accuracy)}}
                        </div>
                        <div class="score-item">
                            <div class="score-header">
                                <h5>Topic Coverage</h5>
                                <span class="score-badge ${{coverageClass}}">
                                    ${{(evaluation.topic_coverage.coverage_score * 100).toFixed(0)}}%
                                </span>
                            </div>
                            <div class="score-reason">${{convertLineBreaks(evaluation.topic_coverage.reason)}}</div>
                        </div>
                    </div>
                    </div>
                </div>
            `;
        }}

        function initializeEntityColors() {{
            // Pre-process all entities to assign consistent colors
            const allEntities = new Set();

            evaluationData.evaluation_outputs.forEach(evaluation => {{
                const entities = evaluation.entities;

                // Collect all unique entities from the structure
                Object.values(entities).forEach(entityGroup => {{
                    if (Array.isArray(entityGroup)) {{
                        entityGroup.forEach(entity => {{
                            if (entity.trigger_variable) {{
                                allEntities.add(entity.trigger_variable);
                            }}
                            if (entity.consequence_variable) {{
                                allEntities.add(entity.consequence_variable);
                            }}
                        }});
                    }}
                }});
            }});

            // Assign colors to all unique entities
            Array.from(allEntities).sort().forEach(entity => {{
                getEntityColor(entity);
            }});
        }}

        function calculateSummaryStats() {{
            const evaluations = evaluationData.evaluation_outputs;
            const totalEvaluations = evaluations.length;

            const avgAccuracy = evaluations.reduce((sum, eval) => sum + eval.accuracy.accuracy_mean, 0) / totalEvaluations;
            const avgCoverage = evaluations.reduce((sum, eval) => sum + eval.topic_coverage.coverage_score, 0) / totalEvaluations;
            const overallScore = (avgAccuracy + avgCoverage) / 2;

            document.getElementById('total-evaluations').textContent = totalEvaluations;
            document.getElementById('avg-accuracy').textContent = avgAccuracy.toFixed(2);
            document.getElementById('avg-coverage').textContent = avgCoverage.toFixed(2);
            document.getElementById('overall-score').textContent = overallScore.toFixed(2);
        }}

        function renderEvaluations() {{
            const container = document.getElementById('evaluations-container');
            const evaluationsHtml = evaluationData.evaluation_outputs
                .map(evaluation => renderEvaluation(evaluation))
                .join('');

            container.innerHTML = evaluationsHtml;
        }}

        function toggleEvaluation(headerElement) {{
            const content = headerElement.nextElementSibling;
            const isCollapsed = headerElement.classList.contains('collapsed');

            if (isCollapsed) {{
                headerElement.classList.remove('collapsed');
                content.classList.remove('collapsed');
            }} else {{
                headerElement.classList.add('collapsed');
                content.classList.add('collapsed');
            }}
        }}

        // JSON data embedded in the page
        const evaluationData = {json_data};

        // Initialize the page
        document.addEventListener('DOMContentLoaded', function() {{
            initializeEntityColors();
            calculateSummaryStats();
            renderEvaluations();
        }});
        """

    def generate_html(self, css_filename: str = "styles.css") -> str:
        """Generate HTML content for the report."""
        javascript_content = self.generate_javascript()

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Constitutional QA Agent Evaluation Results</title>
            <link rel="stylesheet" href="{css_filename}">
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Constitutional QA Agent Evaluation Results</h1>
                    <p>
                        Comprehensive analysis of LLM responses to health insurance 
                        queries with constitutional axioms
                    </p>
                </div>

                <div class="summary">
                    <h2>Summary Statistics</h2>
                    <div class="summary-grid">
                        <div class="summary-card">
                            <h3 id="total-evaluations">0</h3>
                            <p>Total Evaluations</p>
                        </div>
                        <div class="summary-card">
                            <h3 id="avg-accuracy">0.00</h3>
                            <p>Average Accuracy</p>
                        </div>
                        <div class="summary-card">
                            <h3 id="avg-coverage">0.00</h3>
                            <p>Average Topic Coverage</p>
                        </div>
                        <div class="summary-card">
                            <h3 id="overall-score">0.00</h3>
                            <p>Overall Performance</p>
                        </div>
                    </div>
                </div>

                <div id="evaluations-container">
                    <!-- Evaluations will be populated by JavaScript -->
                </div>
            </div>

            <script>
        {javascript_content}
            </script>
        </body>
        </html>
        """

    def generate_report(self):
        """Generate evaluation report from data."""
        print(f"Generating report from data at: {self.data_path}")

        # Check if input file exists
        if not os.path.exists(self.data_path):
            print(f"Error: JSON file '{self.data_path}' not found.")
            return

        # Load evaluation data
        print(f"Loading evaluation data from {self.data_path}...")
        self.load_json_data()

        # Determine output directory
        if self.output_dir is None:
            # Use the same directory as the input file
            input_path = Path(self.data_path)
            output_path = input_path.parent / "report"
        else:
            output_path = Path(self.output_dir)

        # Create output directory
        output_path.mkdir(exist_ok=True)
        print(f"Output directory: {output_path.absolute()}")

        # Generate CSS file
        css_content = self.generate_css()
        css_file_path = output_path / "styles.css"
        with open(css_file_path, "w", encoding="utf-8") as css_file:
            css_file.write(css_content)
        print(f"Generated CSS file: {css_file_path}")

        # Generate HTML file
        html_content = self.generate_html()
        html_file_path = output_path / "index.html"
        with open(html_file_path, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)
        print(f"Generated HTML file: {html_file_path}")

        print("\nReport generation complete!")
        print(f"Open {html_file_path} in your web browser to view the report.")

    @classmethod
    def create_and_generate(cls, data_path: str, output_dir: str | None = None):
        """Create a Report instance and generate the report.

        This is a convenience class method that creates an instance and
        immediately generates the report.
        """
        report = cls(data_path, output_dir)
        report.generate_report()
        return report


def main():
    """Main entry point for report generation."""
    parser = argparse.ArgumentParser(description="Generate evaluation reports")
    parser.add_argument(
        "--data_path", required=True, help="Path to the evaluation data JSON file"
    )
    parser.add_argument(
        "--output_dir",
        help=(
            "Output directory for generated files "
            "(default: same directory as input + '/report')"
        ),
    )

    args = parser.parse_args()
    Report.create_and_generate(args.data_path, args.output_dir)


if __name__ == "__main__":
    main()
