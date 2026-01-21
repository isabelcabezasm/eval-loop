"""
Tests for axiom and reality reference evaluation functionality.

This module tests:
- Precision and recall calculation for references
- Axiom reference extraction from LLM answers
- Reality reference extraction from LLM answers
- Reference evaluation results models
- Statistics calculation for reference metrics
"""

import re
from typing import Any

import pytest
from pytest import approx  # type: ignore[reportUnknownMemberType]

from eval.eval import (
    AXIOM_REFERENCE_PATTERN as AXIOM_PATTERN,
)
from eval.eval import (
    REALITY_REFERENCE_PATTERN as REALITY_PATTERN,
)
from eval.eval import (
    calculate_precision_recall,
    evaluate_axiom_references,
    evaluate_reality_references,
)
from eval.models import (
    AxiomPrecisionMetric,
    AxiomRecallMetric,
    AxiomReferenceResults,
    AxiomReferences,
    RealityPrecisionMetric,
    RealityRecallMetric,
    RealityReferenceResults,
    RealityReferences,
)

# =============================================================================
# Test Data
# =============================================================================

# Sample axiom references for testing
SAMPLE_AXIOMS_EXPECTED: AxiomReferences = ["A-001", "A-002", "A-003"]
SAMPLE_AXIOMS_FOUND: AxiomReferences = ["A-001", "A-002", "A-004"]

# Sample reality references for testing
SAMPLE_REALITY_EXPECTED: RealityReferences = ["R-001", "R-002"]
SAMPLE_REALITY_FOUND: RealityReferences = ["R-001", "R-003"]

# =============================================================================
# Tests for Precision/Recall Calculation
# =============================================================================


@pytest.mark.parametrize(
    ("found", "expected", "expected_precision", "expected_recall"),
    [
        # Perfect match
        (["A-001", "A-002"], ["A-001", "A-002"], 1.0, 1.0),
        # Both empty
        ([], [], 1.0, 1.0),
        # Found empty, expected not empty
        ([], ["A-001", "A-002"], 0.0, 0.0),
        # Found not empty, expected empty
        (["A-001"], [], 0.0, 0.0),
        # Partial overlap (2/3 each, rounded to 4 decimals)
        (
            ["A-001", "A-002", "A-004"],
            ["A-001", "A-002", "A-003"],
            0.6667,
            0.6667,
        ),
        # No overlap
        (["A-001", "A-002"], ["A-003", "A-004"], 0.0, 0.0),
        # All found correct but missing some (precision=1, recall=1/3 rounded)
        (["A-001"], ["A-001", "A-002", "A-003"], 1.0, 0.3333),
        # Found more than expected (precision=0.5, recall=1)
        (["A-001", "A-002", "A-003", "A-004"], ["A-001", "A-002"], 0.5, 1.0),
        # Duplicates in found (set removes them)
        (["A-001", "A-001", "A-002"], ["A-001", "A-002"], 1.0, 1.0),
    ],
    ids=[
        "perfect_match",
        "both_empty",
        "found_empty",
        "expected_empty",
        "partial_overlap",
        "no_overlap",
        "all_correct_missing_some",
        "found_more_than_expected",
        "duplicates_handled",
    ],
)
def test_precision_recall_calculation(
    found: list[str],
    expected: list[str],
    expected_precision: float,
    expected_recall: float,
) -> None:
    """Test precision and recall calculation for various scenarios."""
    precision, recall = calculate_precision_recall(found, expected)
    assert precision == approx(expected_precision)
    assert recall == approx(expected_recall)


# =============================================================================
# Tests for Reference Extraction
# =============================================================================


@pytest.mark.parametrize(
    ("text", "pattern", "expected_refs"),
    [
        # Single axiom
        (
            "Based on [A-001], the interest rate affects borrowing.",
            AXIOM_PATTERN,
            ["[A-001]"],
        ),
        # Multiple axioms
        (
            "According to [A-001] and [A-002], markets are volatile. [A-015].",
            AXIOM_PATTERN,
            ["[A-001]", "[A-002]", "[A-015]"],
        ),
        # No axioms
        ("The economy is doing well.", AXIOM_PATTERN, []),
        # Various number lengths
        (
            "[A-1] [A-12] [A-123] [A-1234]",
            AXIOM_PATTERN,
            ["[A-1]", "[A-12]", "[A-123]", "[A-1234]"],
        ),
        # Invalid patterns ignored
        ("[B-001] [A001] A-001 [A-] [A-abc]", AXIOM_PATTERN, []),
        # Duplicate axioms extracted separately
        (
            "[A-001] is important. As mentioned in [A-001], this is key.",
            AXIOM_PATTERN,
            ["[A-001]", "[A-001]"],
        ),
        # Single reality
        (
            "Based on [R-001], Switzerland's inflation is 2.1%.",
            REALITY_PATTERN,
            ["[R-001]"],
        ),
        # Multiple realities
        (
            "Given [R-001] and [R-002], the outlook is stable. See [R-007].",
            REALITY_PATTERN,
            ["[R-001]", "[R-002]", "[R-007]"],
        ),
        # No realities
        ("The data shows positive trends.", REALITY_PATTERN, []),
    ],
    ids=[
        "single_axiom",
        "multiple_axioms",
        "no_axioms",
        "various_number_lengths",
        "invalid_patterns",
        "duplicate_axioms",
        "single_reality",
        "multiple_realities",
        "no_realities",
    ],
)
def test_reference_extraction(
    text: str, pattern: str, expected_refs: list[str]
) -> None:
    """Test reference extraction from text using regex patterns."""
    found = re.findall(pattern, text)
    assert found == expected_refs


def test_mixed_axiom_and_reality_extraction() -> None:
    """Extract both axiom and reality references from same text."""
    text = "Based on [A-001] and [R-001], with [A-002] and [R-002]."
    axioms = re.findall(AXIOM_PATTERN, text)
    realities = re.findall(REALITY_PATTERN, text)
    assert axioms == ["[A-001]", "[A-002]"]
    assert realities == ["[R-001]", "[R-002]"]


# =============================================================================
# Tests for Reference Results Models
# =============================================================================


def test_create_valid_axiom_results() -> None:
    """Create a valid AxiomReferenceResults instance."""
    result = AxiomReferenceResults(
        references_found=["A-001", "A-002"],
        references_expected=["A-001", "A-003"],
        precision=0.5,
        recall=0.5,
    )
    assert result.references_found == ["A-001", "A-002"]
    assert result.references_expected == ["A-001", "A-003"]
    assert result.precision == 0.5
    assert result.recall == 0.5


def test_create_valid_reality_results() -> None:
    """Create a valid RealityReferenceResults instance."""
    result = RealityReferenceResults(
        references_found=["R-001"],
        references_expected=["R-001", "R-002"],
        precision=1.0,
        recall=0.5,
    )
    assert result.references_found == ["R-001"]
    assert result.references_expected == ["R-001", "R-002"]
    assert result.precision == 1.0
    assert result.recall == 0.5


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("precision", 1.5),
        ("precision", -0.1),
        ("recall", 1.5),
        ("recall", -0.1),
    ],
    ids=[
        "precision_above_1",
        "precision_below_0",
        "recall_above_1",
        "recall_below_0",
    ],
)
def test_reference_results_validation_bounds(
    field: str, invalid_value: float
) -> None:
    """Precision and recall must be between 0.0 and 1.0."""
    kwargs: dict[str, Any] = {
        "references_found": [],
        "references_expected": [],
        "precision": 0.5,
        "recall": 0.5,
    }
    kwargs[field] = invalid_value
    with pytest.raises(ValueError):
        _ = AxiomReferenceResults(**kwargs)


def test_empty_references() -> None:
    """Create results with empty reference lists."""
    result = AxiomReferenceResults(
        references_found=[],
        references_expected=[],
        precision=1.0,
        recall=1.0,
    )
    assert result.references_found == []
    assert result.references_expected == []


def test_reality_inherits_from_axiom_results() -> None:
    """RealityReferenceResults inherits from AxiomReferenceResults."""
    result = RealityReferenceResults(
        references_found=[],
        references_expected=[],
        precision=0.0,
        recall=0.0,
    )
    assert isinstance(result, AxiomReferenceResults)


# =============================================================================
# Tests for Reference Evaluation Functions
# =============================================================================


@pytest.mark.parametrize(
    ("found_refs", "expected_refs", "exp_precision", "exp_recall", "ref_type"),
    [
        # Axiom: bracket normalization
        (["[A-001]", "[A-002]"], ["A-001", "A-002"], 1.0, 1.0, "axiom"),
        # Axiom: partial match
        (["[A-001]", "[A-003]"], ["A-001", "A-002"], 0.5, 0.5, "axiom"),
        # Axiom: empty found
        ([], ["A-001", "A-002"], 0.0, 0.0, "axiom"),
        # Axiom: empty expected
        (["[A-001]"], [], 0.0, 0.0, "axiom"),
        # Axiom: both empty
        ([], [], 1.0, 1.0, "axiom"),
        # Reality: bracket normalization
        (["[R-001]", "[R-002]"], ["R-001", "R-002"], 1.0, 1.0, "reality"),
        # Reality: partial match
        (["[R-001]", "[R-003]"], ["R-001", "R-002"], 0.5, 0.5, "reality"),
        # Reality: both empty
        ([], [], 1.0, 1.0, "reality"),
    ],
    ids=[
        "axiom_bracket_normalization",
        "axiom_partial_match",
        "axiom_empty_found",
        "axiom_empty_expected",
        "axiom_both_empty",
        "reality_bracket_normalization",
        "reality_partial_match",
        "reality_both_empty",
    ],
)
def test_reference_evaluation(
    found_refs: list[str],
    expected_refs: list[str],
    exp_precision: float,
    exp_recall: float,
    ref_type: str,
) -> None:
    """Test reference evaluation for both axiom and reality types."""
    if ref_type == "axiom":
        result = evaluate_axiom_references(found_refs, expected_refs)
    else:
        result = evaluate_reality_references(found_refs, expected_refs)

    assert result.precision == approx(exp_precision)
    assert result.recall == approx(exp_recall)


def test_axiom_evaluation_removes_duplicates() -> None:
    """Duplicate found references are deduplicated."""
    result = evaluate_axiom_references(
        real_axioms=["[A-001]", "[A-001]", "[A-002]"],
        expected_axioms=["A-001", "A-002"],
    )
    assert len(result.references_found) == 2
    assert result.precision == 1.0
    assert result.recall == 1.0


# =============================================================================
# Tests for Metric Models
# =============================================================================


@pytest.mark.parametrize(
    ("metric_class", "mean", "std"),
    [
        (AxiomPrecisionMetric, 0.85, 0.1),
        (AxiomRecallMetric, 0.75, 0.15),
        (RealityPrecisionMetric, 0.9, 0.05),
        (RealityRecallMetric, 0.8, 0.12),
    ],
    ids=[
        "axiom_precision",
        "axiom_recall",
        "reality_precision",
        "reality_recall",
    ],
)
def test_metric_model_creation(
    metric_class: type, mean: float, std: float
) -> None:
    """Test creating metric models with mean and std."""
    metric = metric_class(mean=mean, std=std)
    assert metric.mean == mean
    assert metric.std == std


def test_metric_serialization() -> None:
    """Metrics can be serialized to dict."""
    metric = AxiomPrecisionMetric(mean=0.85, std=0.1)
    data = metric.model_dump()
    assert data == {"mean": 0.85, "std": 0.1}


# =============================================================================
# Tests for Statistics Calculation
# =============================================================================


@pytest.mark.parametrize(
    ("scores", "expected_mean", "expected_std"),
    [
        # Normal case
        ([0.8, 0.9, 0.7, 1.0], 0.85, 0.1118),
        # Single score
        ([0.85], 0.85, 0.0),
        # All same scores
        ([0.8, 0.8, 0.8, 0.8], 0.8, 0.0),
    ],
    ids=["normal_case", "single_score", "identical_scores"],
)
def test_statistics_calculation(
    scores: list[float], expected_mean: float, expected_std: float
) -> None:
    """Test mean and standard deviation calculation."""
    mean = sum(scores) / len(scores)
    assert mean == approx(expected_mean)

    if len(scores) <= 1:
        std = 0.0
    else:
        variance = sum((score - mean) ** 2 for score in scores) / len(scores)
        std = variance**0.5
    assert std == approx(expected_std, rel=0.01)


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.parametrize(
    (
        "llm_answer",
        "expected_refs",
        "pattern",
        "eval_func",
        "expected_found",
        "exp_precision",
        "exp_recall",
    ),
    [
        # Axiom evaluation workflow
        (
            """
            Based on the economic principles described in [A-001] and [A-002],
            we can see that interest rates affect borrowing. Additionally,
            [A-003] explains how inflation impacts purchasing power.
            """,
            ["A-001", "A-002", "A-004"],
            AXIOM_PATTERN,
            evaluate_axiom_references,
            ["[A-001]", "[A-002]", "[A-003]"],
            0.6667,
            0.6667,
        ),
        # Reality evaluation workflow
        (
            """
            According to current data [R-001], Switzerland's inflation is 2.1%.
            The unemployment rate [R-002] stands at 2.3%.
            """,
            ["R-001", "R-002", "R-003"],
            REALITY_PATTERN,
            evaluate_reality_references,
            ["[R-001]", "[R-002]"],
            1.0,
            0.6667,
        ),
    ],
    ids=["axiom_workflow", "reality_workflow"],
)
def test_full_evaluation_workflow(
    llm_answer: str,
    expected_refs: list[str],
    pattern: str,
    eval_func: Any,
    expected_found: list[str],
    exp_precision: float,
    exp_recall: float,
) -> None:
    """Test complete evaluation workflow from LLM text to results."""
    # Extract references from LLM answer
    found_raw = re.findall(pattern, llm_answer)
    assert found_raw == expected_found

    # Evaluate
    result = eval_func(found_raw, expected_refs)
    assert result.precision == approx(exp_precision)
    assert result.recall == approx(exp_recall)


def test_mixed_references_in_answer() -> None:
    """Test extracting both axiom and reality references from same text."""
    llm_answer = """
    Based on [A-001] and current data [R-001], we see that [A-002]
    applies here. The reality [R-002] confirms this analysis.
    """
    axioms_found = re.findall(AXIOM_PATTERN, llm_answer)
    realities_found = re.findall(REALITY_PATTERN, llm_answer)
    assert axioms_found == ["[A-001]", "[A-002]"]
    assert realities_found == ["[R-001]", "[R-002]"]

    # Evaluate separately
    axiom_result = evaluate_axiom_references(axioms_found, ["A-001", "A-002"])
    reality_result = evaluate_reality_references(
        realities_found, ["R-001", "R-002"]
    )
    assert axiom_result.precision == 1.0
    assert axiom_result.recall == 1.0
    assert reality_result.precision == 1.0
    assert reality_result.recall == 1.0
