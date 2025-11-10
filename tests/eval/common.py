from eval.models import (
    AccuracyEvaluationResults,
    Entity,
    EntityAccuracy,
    EntityExtraction,
)

sample_entity_extraction_result = EntityExtraction(
    user_query_entities=[
        Entity(
            trigger_variable="interest_rate",
            consequence_variable="borrowing_cost",
        ),
        Entity(
            trigger_variable="inflation",
            consequence_variable="purchasing_power",
        ),
    ],
    llm_answer_entities=[
        Entity(
            trigger_variable="monetary_policy",
            consequence_variable="investment_decisions",
        ),
        Entity(
            trigger_variable="unemployment",
            consequence_variable="consumer_spending",
        ),
    ],
    expected_answer_entities=[
        Entity(
            trigger_variable="interest_rate",
            consequence_variable="borrowing_cost",
        ),
        Entity(
            trigger_variable="unemployment",
            consequence_variable="purchasing_power",
        ),
    ],
)

sample_accuracy_evaluation_results = AccuracyEvaluationResults(
    entity_accuracies=[
        EntityAccuracy(
            entity=Entity(
                trigger_variable="interest_rate",
                consequence_variable="borrowing_cost",
            ),
            reason=(
                "The entity interest_rate->borrowing_cost is accurately "
                "represented in both answers with similar semantic meaning."
            ),
            score=1.0,
        ),
        EntityAccuracy(
            entity=Entity(
                trigger_variable="unemployment",
                consequence_variable="purchasing_power",
            ),
            reason=(
                "The entity unemployment->purchasing_power is partially "
                "represented; LLM mentions economic impact but not "
                "purchasing power specifically."
            ),
            score=0.7,
        ),
    ],
    accuracy_mean=0.85,
)
