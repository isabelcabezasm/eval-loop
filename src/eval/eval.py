import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from core.paths import root
from eval.dependencies import qa_eval_engine
from eval.models import (
    AxiomPrecisionMetric,
    AxiomRecallMetric,
    AxiomReferenceResults,
    AxiomReferences,
    EvaluationSampleInput,
    EvaluationSampleOutput,
    RealityPrecisionMetric,
    RealityRecallMetric,
    RealityReferenceResults,
    RealityReferences,
)
from eval.report_generation.report import Report

AXIOM_REFERENCE_PATTERN = r"\[A-\d+\]"
REALITY_REFERENCE_PATTERN = r"\[R-\d+\]"


def calculate_precision_recall(
    found: list[str], expected: list[str]
) -> tuple[float, float]:
    """Calculate precision and recall for reference evaluation.

    Precision measures how many of the found references are correct.
    Recall measures how many of the expected references were found.

    Args:
        found: List of references found in the answer.
        expected: List of expected references.

    Returns:
        Tuple of (precision, recall) scores between 0.0 and 1.0.
        Returns (1.0, 1.0) when both lists are empty.

    Examples:
        >>> calculate_precision_recall(["A-001", "A-002"], ["A-001", "A-002"])
        (1.0, 1.0)
        >>> calculate_precision_recall(["A-001", "A-003"], ["A-001", "A-002"])
        (0.5, 0.5)
        >>> calculate_precision_recall([], [])
        (1.0, 1.0)
    """
    found_set = set(found)
    expected_set = set(expected)

    # If both are empty, the answer is correct
    # (nothing expected, nothing found)
    if not found_set and not expected_set:
        return 1.0, 1.0

    true_positives = len(found_set & expected_set)
    precision = round(true_positives / len(found_set), 4) if found_set else 0.0
    recall = (
        round(true_positives / len(expected_set), 4) if expected_set else 0.0
    )
    return precision, recall


def evaluate_axiom_references(
    real_axioms: AxiomReferences, expected_axioms: AxiomReferences
) -> AxiomReferenceResults:
    """Evaluate axiom references found vs expected.

    Extracts and normalizes axiom references from the LLM answer,
    removing brackets (e.g., "[A-001]" -> "A-001"), then calculates
    precision and recall against the expected references.

    Args:
        real_axioms: Axiom references found in the LLM answer,
            typically extracted via regex (e.g., ["[A-001]", "[A-002]"]).
        expected_axioms: Expected axiom references without brackets
            (e.g., ["A-001", "A-002"]).

    Returns:
        AxiomReferenceResults containing the normalized found references,
        expected references, and precision/recall scores.

    Examples:
        >>> result = evaluate_axiom_references(
        ...     ["[A-001]", "[A-002]"], ["A-001", "A-002"]
        ... )
        >>> result.precision
        1.0
        >>> result.recall
        1.0
    """
    # Normalize found axioms: "[A-001]" -> "A-001"
    normalized_found = list(set(ref.strip("[]") for ref in real_axioms))

    precision, recall = calculate_precision_recall(
        normalized_found, expected_axioms
    )
    return AxiomReferenceResults(
        references_found=normalized_found,
        references_expected=expected_axioms,
        precision=precision,
        recall=recall,
    )


def evaluate_reality_references(
    real_reality: RealityReferences, expected_reality: RealityReferences
) -> RealityReferenceResults:
    """Evaluate reality references found vs expected.

    Extracts and normalizes reality references from the LLM answer,
    removing brackets (e.g., "[R-001]" -> "R-001"), then calculates
    precision and recall against the expected references.

    Args:
        real_reality: Reality references found in the LLM answer,
            typically extracted via regex (e.g., ["[R-001]", "[R-002]"]).
        expected_reality: Expected reality references without brackets
            (e.g., ["R-001", "R-002"]).

    Returns:
        RealityReferenceResults containing the normalized found references,
        expected references, and precision/recall scores.

    Examples:
        >>> result = evaluate_reality_references(
        ...     ["[R-001]", "[R-002]"], ["R-001", "R-002"]
        ... )
        >>> result.precision
        1.0
        >>> result.recall
        1.0
    """
    # Normalize found reality refs: "[R-001]" -> "R-001"
    normalized_found = list(set(ref.strip("[]") for ref in real_reality))

    precision, recall = calculate_precision_recall(
        normalized_found, expected_reality
    )
    return RealityReferenceResults(
        references_found=normalized_found,
        references_expected=expected_reality,
        precision=precision,
        recall=recall,
    )


class Metric(BaseModel):
    """
    A data model representing statistical metrics with mean and standard
    deviation.

    Attributes:
        mean (float): The arithmetic mean of the data. std (float): The
        standard deviation of the data.
    """

    mean: float
    std: float


class AccuracyMetric(Metric):
    """
    A metric class for calculating accuracy of predictions.

    This metric computes the accuracy as the fraction of predictions that match
    the true labels. Accuracy is calculated as the number of correct
    predictions divided by the total number of predictions.

    The metric can be used for classification tasks where exact matches between
    predicted and actual values are required.

    Returns:
        float: Accuracy score between 0.0 and 1.0, where 1.0 represents perfect
        accuracy.
    """


class CoverageMetric(Metric):
    """
    A metric class for measuring topic coverage during evaluation.

    This metric tracks the degree to which responses cover expected topics or
    concepts in the evaluation samples. It provides insights into how
    comprehensively the system addresses the relevant subject matter.

    Attributes:
        Inherits all attributes from the base Metric class.

    Methods:
        Inherits all methods from the base Metric class and may override
        specific methods to implement coverage-specific calculations.

    Usage:
        Used to monitor and report topic coverage statistics during evaluation
        workflows.
    """


class QuestionAnswerFunction(Protocol):
    """
    Protocol for functions that generate answers from user queries.

    This protocol defines the interface for async functions that take a user's
    query string and return a generated answer. Implementations should process
    the query and generate contextually relevant responses based on the input.

    Methods:
        __call__(*, query: str) -> str: Async method that processes a query and
        returns a generated answer string.

    Example:
        >>> async def my_qa_function(*, query: str) -> str:
        ...     return f"Generated answer for: {query}"
        >>>
        >>> # Usage
        >>> answer = await my_qa_function(query="What if it rains?")
    """

    # this is just the protocol

    async def __call__(self,
                       *,
                       query: str) -> str:  # pyright: ignore[reportReturnType]
        """
        Takes a user query and returns a generated answer.

        Args:
            query: The user's query string

        Returns:
            A generated answer as a string
        """


class EvaluationResult(BaseModel):
    """
    Represents the complete result of an evaluation run.

    This class encapsulates all outputs and metrics from evaluating a model or
    system, providing a comprehensive view of performance across multiple
    dimensions.

    Attributes:
        evaluation_outputs (list[EvaluationSampleOutput]): A list of individual
        sample evaluation results, containing the detailed outputs for each
        test case. accuracy (AccuracyMetric): Metric measuring the correctness
        of predictions or responses across the evaluation dataset.
        topic_coverage (CoverageMetric): Metric measuring how well the
        evaluation spans different topics or categories in the domain.
    """

    evaluation_outputs: list[EvaluationSampleOutput]
    accuracy: AccuracyMetric
    topic_coverage: CoverageMetric
    axiom_precision_metric: AxiomPrecisionMetric
    axiom_recall_metric: AxiomRecallMetric
    reality_precision_metric: RealityPrecisionMetric
    reality_recall_metric: RealityRecallMetric


async def evaluate_answer(
    sample_input: EvaluationSampleInput, llm_answer: str
) -> EvaluationSampleOutput:
    """Evaluate the quality of an LLM's answer against the expected output.

    This function assesses an LLM-generated answer by analyzing multiple
    metrics including accuracy, topic coverage, and reference evaluation
    (axiom and reality references).

    Args:
        sample_input: The evaluation sample containing the query,
            expected answer, and expected references.
        llm_answer: The LLM-generated answer to evaluate.

    Returns:
        EvaluationSampleOutput containing the input, LLM response,
        extracted entities, and all computed metrics.
    """

    engine = qa_eval_engine()

    entities = await engine.entity_extraction(
        user_query=sample_input.query,
        llm_answer=llm_answer,
        expected_answer=sample_input.expected_answer,
    )

    accuracy = await engine.accuracy_evaluation(
        entity_list=entities,
        llm_answer=llm_answer,
        expected_answer=sample_input.expected_answer,
    )

    topic_coverage = await engine.topic_coverage_evaluation(
        entity_list=entities
    )

    return EvaluationSampleOutput(
        input=sample_input,
        llm_response=llm_answer,
        entities=entities,
        accuracy=accuracy,
        topic_coverage=topic_coverage,
        axiom_references=evaluate_axiom_references(
            re.findall(AXIOM_REFERENCE_PATTERN, llm_answer),
            sample_input.axioms_used,
        ),
        reality_references=evaluate_reality_references(
            re.findall(REALITY_REFERENCE_PATTERN, llm_answer),
            sample_input.reality_used,
        ),
    )


def calculate_stats(
    evaluation_results: list[EvaluationSampleOutput],
) -> EvaluationResult:
    """
    Calculate statistical metrics from evaluation results.

    Args:
        evaluation_results: Collection of evaluation outputs to analyze

    Returns:
        EvaluationResult: Object containing the evaluation outputs and computed
        statistical metrics including accuracy and topic coverage.
    """
    if not evaluation_results:
        return EvaluationResult(
            evaluation_outputs=[],
            accuracy=AccuracyMetric(mean=0.0, std=0.0),
            topic_coverage=CoverageMetric(mean=0.0, std=0.0),
            axiom_precision_metric=AxiomPrecisionMetric(mean=0.0, std=0.0),
            axiom_recall_metric=AxiomRecallMetric(mean=0.0, std=0.0),
            reality_precision_metric=RealityPrecisionMetric(mean=0.0, std=0.0),
            reality_recall_metric=RealityRecallMetric(mean=0.0, std=0.0),
        )

    # Calculate accuracy statistics
    accuracy_scores = [
        result.accuracy.accuracy_mean for result in evaluation_results
    ]
    accuracy_mean = sum(accuracy_scores) / len(accuracy_scores)
    accuracy_variance = sum(
        (score - accuracy_mean) ** 2 for score in accuracy_scores
    ) / len(accuracy_scores)
    accuracy_std = accuracy_variance**0.5 if len(accuracy_scores) > 1 else 0.0

    # Calculate topic coverage statistics
    coverage_scores = [
        result.topic_coverage.coverage_score for result in evaluation_results
    ]
    coverage_mean = sum(coverage_scores) / len(coverage_scores)
    coverage_variance = sum(
        (score - coverage_mean) ** 2 for score in coverage_scores
    ) / len(coverage_scores)
    coverage_std = coverage_variance**0.5 if len(coverage_scores) > 1 else 0.0

    # Calculate axiom precision statistics
    axiom_precision_scores = [
        result.axiom_references.precision for result in evaluation_results
    ]
    axiom_precision_mean = sum(axiom_precision_scores) / len(
        axiom_precision_scores
    )
    axiom_precision_variance = sum(
        (score - axiom_precision_mean) ** 2 for score in axiom_precision_scores
    ) / len(axiom_precision_scores)
    axiom_precision_std = (
        axiom_precision_variance**0.5
        if len(axiom_precision_scores) > 1
        else 0.0
    )

    # Calculate axiom recall statistics
    axiom_recall_scores = [
        result.axiom_references.recall for result in evaluation_results
    ]
    axiom_recall_mean = sum(axiom_recall_scores) / len(axiom_recall_scores)
    axiom_recall_variance = sum(
        (score - axiom_recall_mean) ** 2 for score in axiom_recall_scores
    ) / len(axiom_recall_scores)
    axiom_recall_std = (
        axiom_recall_variance**0.5 if len(axiom_recall_scores) > 1 else 0.0
    )

    # Calculate reality precision statistics
    reality_precision_scores = [
        result.reality_references.precision for result in evaluation_results
    ]
    reality_precision_mean = sum(reality_precision_scores) / len(
        reality_precision_scores
    )
    reality_precision_variance = sum(
        (score - reality_precision_mean) ** 2
        for score in reality_precision_scores
    ) / len(reality_precision_scores)
    reality_precision_std = (
        reality_precision_variance**0.5
        if len(reality_precision_scores) > 1
        else 0.0
    )

    # Calculate reality recall statistics
    reality_recall_scores = [
        result.reality_references.recall for result in evaluation_results
    ]
    reality_recall_mean = sum(reality_recall_scores) / len(
        reality_recall_scores
    )
    reality_recall_variance = sum(
        (score - reality_recall_mean) ** 2 for score in reality_recall_scores
    ) / len(reality_recall_scores)
    reality_recall_std = (
        reality_recall_variance**0.5 if len(reality_recall_scores) > 1 else 0.0
    )

    return EvaluationResult(
        evaluation_outputs=evaluation_results,
        accuracy=AccuracyMetric(mean=accuracy_mean, std=accuracy_std),
        topic_coverage=CoverageMetric(mean=coverage_mean, std=coverage_std),
        axiom_precision_metric=AxiomPrecisionMetric(
            mean=axiom_precision_mean, std=axiom_precision_std
        ),
        axiom_recall_metric=AxiomRecallMetric(
            mean=axiom_recall_mean, std=axiom_recall_std
        ),
        reality_precision_metric=RealityPrecisionMetric(
            mean=reality_precision_mean, std=reality_precision_std
        ),
        reality_recall_metric=RealityRecallMetric(
            mean=reality_recall_mean, std=reality_recall_std
        ),
    )


async def run_evaluation(
    *,
    question_answer_fn: QuestionAnswerFunction,
    input_data_path: Path | None = None,
    output_data_path: Path | None = None,
) -> None:
    """Run the full evaluation pipeline.

    Executes the evaluation process by reading input samples, generating
    LLM responses, computing evaluation metrics, and generating a report.

    Args:
        question_answer_fn: Async function that takes a query and returns
            an LLM-generated answer.
        input_data_path: Path to the input JSON file containing evaluation
            samples. Defaults to 'data/eval_dataset.json'.
        ouptput_data_path: Path to the output directory for results.
            Defaults to 'runs/{timestamp}'.

    Side Effects:
        - Creates output directory if it doesn't exist.
        - Writes individual result markdown files for each sample.
        - Writes evaluation_results.json with aggregated metrics.
        - Generates an HTML report in the output directory.
    """

    input_path = input_data_path or root() / "data/eval_dataset.json"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_data_path or root() / f"runs/{timestamp}"
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Running evaluation with data path: {input_path}")
    print(f"Running evaluation with output data path: {output_path}")

    async def process_sample(sample_data: str) -> EvaluationSampleOutput:
        parsed_input = EvaluationSampleInput.model_validate(sample_data)

        llm_response = await question_answer_fn(query=parsed_input.query)

        _ = (output_path / f"results_{parsed_input.id}.md").write_text(
            llm_response
        )
        return await evaluate_answer(parsed_input, llm_response)

    evaluation_results = await asyncio.gather(
        *map(process_sample, json.loads(input_path.read_text()))
    )
    result = calculate_stats(evaluation_results)

    # save the results
    result_path = output_path / "evaluation_results.json"
    _ = result_path.write_text(result.model_dump_json(indent=4))

    # generate a report in the same folder with the results
    report: Report = Report(data_path=str(result_path))
    report.generate_report()

    # Determine actual report directory
    if report.output_dir is None:
        report_dir = report.data_path.parent / "report"
    else:
        report_dir = report.output_dir

    print(f"Saved evaluation results to: {result_path}")
    print(f"Generated evaluation report in: {report_dir}")
