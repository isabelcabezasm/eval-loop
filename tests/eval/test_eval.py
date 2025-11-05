"""Tests for eval.py statistics calculation."""

import math
from unittest.mock import Mock

import pytest

from eval.eval import (
    EvaluationResult,
    EvaluationSampleInput,
    EvaluationSampleOutput,
    calculate_stats,
)
from eval.metrics.models import (
    AccuracyEvaluationResults,
    EntityExtraction,
    TopicCoverageEvaluationResults,
)


def create_mock_evaluation_output(accuracy: float, coverage: float):
    """Helper to create a mock EvaluationSampleOutput for testing."""
    mock_input = EvaluationSampleInput(
        id=1,
        query="test query",
        context="test context",
        expected_answer="test answer",
        reasoning=["test"],
        axioms_used=["test"],
    )
    mock_entities = EntityExtraction(
        user_query_entities=[],
        llm_answer_entities=[],
        expected_answer_entities=[],
    )
    mock_accuracy = AccuracyEvaluationResults(
        accuracy_mean=accuracy, entity_accuracies=[]
    )
    mock_coverage = TopicCoverageEvaluationResults(
        coverage_score=coverage, reason="test"
    )

    return EvaluationSampleOutput(
        input=mock_input,
        llm_response="test response",
        entities=mock_entities,
        accuracy=mock_accuracy,
        topic_coverage=mock_coverage,
    )


def test_calculate_stats_empty_results():
    """Test that calculate_stats handles empty results correctly."""
    result = calculate_stats([])

    assert result.evaluation_outputs == []
    assert result.accuracy.mean == 0.0
    assert result.accuracy.std == 0.0
    assert result.topic_coverage.mean == 0.0
    assert result.topic_coverage.std == 0.0


def test_calculate_stats_single_result():
    """Test that calculate_stats handles a single result correctly."""
    evaluation_results = [create_mock_evaluation_output(accuracy=0.8, coverage=0.9)]

    result = calculate_stats(evaluation_results)

    assert len(result.evaluation_outputs) == 1
    assert result.accuracy.mean == 0.8
    assert result.accuracy.std == 0.0  # std should be 0 for single value
    assert result.topic_coverage.mean == 0.9
    assert result.topic_coverage.std == 0.0


def test_calculate_stats_two_results():
    """Test standard deviation calculation with two results using Bessel's correction."""
    # Using two values to test Bessel's correction (N-1)
    evaluation_results = [
        create_mock_evaluation_output(accuracy=0.8, coverage=0.9),
        create_mock_evaluation_output(accuracy=0.6, coverage=0.7),
    ]

    result = calculate_stats(evaluation_results)

    # Mean calculations
    assert result.accuracy.mean == 0.7  # (0.8 + 0.6) / 2
    assert result.topic_coverage.mean == 0.8  # (0.9 + 0.7) / 2

    # Sample standard deviation with Bessel's correction (N-1):
    # For accuracy: values = [0.8, 0.6], mean = 0.7
    # variance = ((0.8-0.7)^2 + (0.6-0.7)^2) / (2-1) = (0.01 + 0.01) / 1 = 0.02
    # std = sqrt(0.02) ≈ 0.141421356
    expected_accuracy_std = math.sqrt(0.02)
    assert math.isclose(
        result.accuracy.std, expected_accuracy_std, rel_tol=1e-9
    ), f"Expected {expected_accuracy_std}, got {result.accuracy.std}"

    # For coverage: values = [0.9, 0.7], mean = 0.8
    # variance = ((0.9-0.8)^2 + (0.7-0.8)^2) / (2-1) = (0.01 + 0.01) / 1 = 0.02
    # std = sqrt(0.02) ≈ 0.141421356
    expected_coverage_std = math.sqrt(0.02)
    assert math.isclose(
        result.topic_coverage.std, expected_coverage_std, rel_tol=1e-9
    ), f"Expected {expected_coverage_std}, got {result.topic_coverage.std}"


def test_calculate_stats_three_results():
    """Test standard deviation calculation with three results."""
    evaluation_results = [
        create_mock_evaluation_output(accuracy=0.8, coverage=0.9),
        create_mock_evaluation_output(accuracy=0.6, coverage=0.7),
        create_mock_evaluation_output(accuracy=0.7, coverage=0.8),
    ]

    result = calculate_stats(evaluation_results)

    # Mean calculations
    assert math.isclose(result.accuracy.mean, 0.7, rel_tol=1e-9)
    assert math.isclose(result.topic_coverage.mean, 0.8, rel_tol=1e-9)

    # Sample standard deviation with Bessel's correction (N-1):
    # For accuracy: values = [0.8, 0.6, 0.7], mean = 0.7
    # variance = ((0.8-0.7)^2 + (0.6-0.7)^2 + (0.7-0.7)^2) / (3-1)
    #          = (0.01 + 0.01 + 0) / 2 = 0.01
    # std = sqrt(0.01) = 0.1
    expected_accuracy_std = 0.1
    assert math.isclose(
        result.accuracy.std, expected_accuracy_std, rel_tol=1e-9
    ), f"Expected {expected_accuracy_std}, got {result.accuracy.std}"

    # For coverage: values = [0.9, 0.7, 0.8], mean = 0.8
    # variance = ((0.9-0.8)^2 + (0.7-0.8)^2 + (0.8-0.8)^2) / (3-1)
    #          = (0.01 + 0.01 + 0) / 2 = 0.01
    # std = sqrt(0.01) = 0.1
    expected_coverage_std = 0.1
    assert math.isclose(
        result.topic_coverage.std, expected_coverage_std, rel_tol=1e-9
    ), f"Expected {expected_coverage_std}, got {result.topic_coverage.std}"


def test_calculate_stats_preserves_evaluation_outputs():
    """Test that calculate_stats preserves the original evaluation outputs."""
    evaluation_results = [
        create_mock_evaluation_output(accuracy=0.8, coverage=0.9),
        create_mock_evaluation_output(accuracy=0.6, coverage=0.7),
    ]

    result = calculate_stats(evaluation_results)

    assert result.evaluation_outputs == evaluation_results
    assert len(result.evaluation_outputs) == 2
