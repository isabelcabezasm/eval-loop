from eval.metrics.dependencies import qa_eval_engine
from eval.metrics.models import EntityExtraction, TopicCoverageEvaluationResults


async def get_topic_coverage(
    *, entity_list: EntityExtraction
) -> TopicCoverageEvaluationResults:
    """
    Evaluate the topic coverage of LLM predictions by comparing expected and
    generated entities.

    This function assesses whether the topics represented by entities in the
    expected answer are covered in the generated answer. It focuses on recall
    (coverage) rather than precision, checking if all expected entities appear
    in some form in the generated entities.

    Args:
        entity_list (EntityExtraction): Extracted entities from user query,
            LLM answer, and expected answer.

    Returns:
        TopicCoverageEvaluationResults: The topic coverage evaluation results.
    """
    return await qa_eval_engine().topic_coverage_evaluation(entity_list)
