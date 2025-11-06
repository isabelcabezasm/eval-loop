import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from core.paths import root
from eval.metrics.accuracy import get_accuracy
from eval.metrics.extract_entities import get_entities
from eval.metrics.models import (
    AccuracyEvaluationResults,
    AccuracyMetric,
    CoverageMetric,
    EntityExtraction,
    EvaluationResult,
    EvaluationSampleInput,
    EvaluationSampleOutput,
    TopicCoverageEvaluationResults,
)
from eval.metrics.topic_coverage import get_topic_coverage
from eval.report_generation.report import Report


class QuestionAnswerFunction(Protocol):
    """
    Protocol for functions that generate answers from user queries.

    This protocol defines the interface for async functions that take a user's query
    string and return a generated answer. Implementations should process the query and
    generate contextually relevant responses based on the input.

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
    async def __call__(self, *, query: str) -> str:  # pyright: ignore[reportReturnType]
        """
        Takes a user query and returns a generated answer.

        Args:
            query: The user's query string

        Returns:
            A generated answer as a string
        """


async def evaluate_answer(
    sample_input: EvaluationSampleInput, llm_answer: str
) -> EvaluationSampleOutput:
    """
    Evaluate the quality of an LLM's answer against the given input.

    This function assesses an LLM-generated answer by analyzing various metrics
    including accuracy and topic coverage, and extracting relevant entities.
    """

    entities = await get_entities(
        user_prompt=sample_input.query,
        llm_answer=llm_answer,
        expected_answer=sample_input.expected_answer,
    )

    accuracy = await get_accuracy(
        entity_list=entities,
        llm_answer=llm_answer,
        expected_answer=sample_input.expected_answer,
    )

    topic_coverage = await get_topic_coverage(entity_list=entities)

    return EvaluationSampleOutput(
        input=sample_input,
        llm_response=llm_answer,
        entities=entities,
        accuracy=accuracy,
        topic_coverage=topic_coverage,
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
        )

    # Calculate accuracy statistics
    accuracy_scores = [result.accuracy.accuracy_mean for result in evaluation_results]
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

    return EvaluationResult(
        evaluation_outputs=evaluation_results,
        accuracy=AccuracyMetric(mean=accuracy_mean, std=accuracy_std),
        topic_coverage=CoverageMetric(mean=coverage_mean, std=coverage_std),
    )


async def run_evaluation(
    *,
    question_answer_fn: QuestionAnswerFunction,
    input_data_path: Path | None = None,
    ouptput_data_path: Path | None = None,
) -> None:
    """
    Run the evaluation process with the given data path.

    Args:
        data_path (str): Path to the data file or directory
    """

    input_path = input_data_path or root() / "data/eval_dataset.json"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = ouptput_data_path or root() / f"runs/{timestamp}"
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Running evaluation with data path: {input_path}")
    print(f"Running evaluation with output data path: {output_path}")

    async def process_sample(sample_data: str) -> EvaluationSampleOutput:
        parsed_input = EvaluationSampleInput.model_validate(sample_data)

        llm_response = await question_answer_fn(query=parsed_input.query)

        _ = (output_path / f"results_{parsed_input.id}.md").write_text(llm_response)
        return await evaluate_answer(parsed_input, llm_response)

    evaluation_results = await asyncio.gather(
        *map(process_sample, json.loads(input_path.read_text()))
    )
    result = calculate_stats(evaluation_results)

    # save the results
    result_path = output_path / "evaluation_results.json"
    _ = result_path.write_text(result.model_dump_json(indent=4))

    # generate a report in the same folder with the results
    report = Report(data_path=str(result_path))
    report.generate_report()

    print(f"Saved evaluation results to: {result_path}")
    print(f"Generated evaluation report in: {output_path}")
