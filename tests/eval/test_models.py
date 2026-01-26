"""
Tests for AxiomItem, RealityItem, and EvaluationResult model extensions.

This module tests:
- AxiomItem model validation and serialization
- RealityItem model validation and serialization
- EvaluationResult with axiom/reality definitions (backward compatibility)
"""

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from eval.models import (
    AccuracyMetric,
    AxiomItem,
    AxiomPrecisionMetric,
    AxiomRecallMetric,
    CoverageMetric,
    EvaluationResult,
    RealityItem,
    RealityPrecisionMetric,
    RealityRecallMetric,
)

# =============================================================================
# Test Data
# =============================================================================

SAMPLE_AXIOM_DATA: dict[str, str] = {
    "id": "A-001",
    "description": (
        "Political instability often disrupts markets and investor confidence."
    ),
}

SAMPLE_REALITY_DATA: dict[str, str] = {
    "id": "R-001",
    "description": (
        "Current inflation rate in Switzerland is 2.1% as of Q3 2024."
    ),
}

SAMPLE_AXIOM_ITEMS = [
    AxiomItem(id="A-001", description="First axiom description."),
    AxiomItem(id="A-002", description="Second axiom description."),
]

SAMPLE_REALITY_ITEMS = [
    RealityItem(id="R-001", description="First reality description."),
    RealityItem(id="R-002", description="Second reality description."),
]


# =============================================================================
# Tests for AxiomItem and RealityItem Models (Parametrized)
# =============================================================================


@pytest.mark.parametrize(
    ("model_class", "sample_data", "expected_id"),
    [
        (AxiomItem, SAMPLE_AXIOM_DATA, "A-001"),
        (RealityItem, SAMPLE_REALITY_DATA, "R-001"),
    ],
    ids=["axiom_item", "reality_item"],
)
def test_item_create_with_valid_data(
    model_class: type[BaseModel],
    sample_data: dict[str, str],
    expected_id: str,
) -> None:
    """Test creating item with valid id and description."""
    item = model_class(**sample_data)

    assert item.id == expected_id  # type: ignore[attr-defined]
    assert item.description == sample_data["description"]  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("model_class", "kwargs", "missing_field"),
    [
        (AxiomItem, {"description": "Some description"}, "id"),
        (AxiomItem, {"id": "A-001"}, "description"),
        (RealityItem, {"description": "Some description"}, "id"),
        (RealityItem, {"id": "R-001"}, "description"),
    ],
    ids=[
        "axiom_missing_id",
        "axiom_missing_description",
        "reality_missing_id",
        "reality_missing_description",
    ],
)
def test_item_missing_field_should_raise_error(
    model_class: type[BaseModel],
    kwargs: dict[str, Any],
    missing_field: str,
) -> None:
    """Test that missing required field raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        model_class(**kwargs)  # type: ignore[arg-type]

    assert missing_field in str(exc_info.value)


@pytest.mark.parametrize(
    ("model_class", "kwargs", "empty_field"),
    [
        (AxiomItem, {"id": "", "description": "Some description"}, "id"),
        (AxiomItem, {"id": "A-001", "description": ""}, "description"),
        (RealityItem, {"id": "", "description": "Some description"}, "id"),
        (RealityItem, {"id": "R-001", "description": ""}, "description"),
    ],
    ids=[
        "axiom_empty_id",
        "axiom_empty_description",
        "reality_empty_id",
        "reality_empty_description",
    ],
)
def test_item_empty_field_should_raise_error(
    model_class: type[BaseModel],
    kwargs: dict[str, str],
    empty_field: str,
) -> None:
    """Test that empty field raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        _ = model_class(**kwargs)

    assert empty_field in str(exc_info.value)


@pytest.mark.parametrize(
    ("model_class", "sample_data"),
    [
        (AxiomItem, SAMPLE_AXIOM_DATA),
        (RealityItem, SAMPLE_REALITY_DATA),
    ],
    ids=["axiom_item", "reality_item"],
)
def test_item_equality(
    model_class: type[BaseModel],
    sample_data: dict[str, str],
) -> None:
    """Test item equality comparison."""
    item1 = model_class(**sample_data)
    item2 = model_class(**sample_data)

    assert item1 == item2


@pytest.mark.parametrize(
    ("model_class", "json_str", "expected_id"),
    [
        (
            AxiomItem,
            '{"id": "A-001", "description": "Test description"}',
            "A-001",
        ),
        (
            RealityItem,
            '{"id": "R-001", "description": "Test description"}',
            "R-001",
        ),
    ],
    ids=["axiom_item", "reality_item"],
)
def test_item_from_json_string(
    model_class: type[BaseModel],
    json_str: str,
    expected_id: str,
) -> None:
    """Test creating item from JSON string."""
    item = model_class.model_validate_json(json_str)

    assert item.id == expected_id  # type: ignore[attr-defined]
    assert item.description == "Test description"  # type: ignore[attr-defined]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def minimal_evaluation_result() -> EvaluationResult:
    """Fixture providing a minimal EvaluationResult for testing."""
    return EvaluationResult(
        evaluation_outputs=[],
        accuracy=AccuracyMetric(mean=0.8, std=0.1),
        topic_coverage=CoverageMetric(mean=0.85, std=0.05),
        axiom_precision_metric=AxiomPrecisionMetric(mean=0.9, std=0.1),
        axiom_recall_metric=AxiomRecallMetric(mean=0.8, std=0.15),
        reality_precision_metric=RealityPrecisionMetric(mean=0.85, std=0.1),
        reality_recall_metric=RealityRecallMetric(mean=0.75, std=0.2),
    )


# =============================================================================
# Tests for EvaluationResult with Definitions
# =============================================================================


def test_evaluation_result_without_definitions(
    minimal_evaluation_result: EvaluationResult,
) -> None:
    """Test EvaluationResult without definitions defaults to None."""
    assert minimal_evaluation_result.axiom_definitions is None
    assert minimal_evaluation_result.reality_definitions is None


def test_evaluation_result_with_axiom_definitions_only(
    minimal_evaluation_result: EvaluationResult,
) -> None:
    """Test EvaluationResult with only axiom definitions."""
    result = minimal_evaluation_result.model_copy(
        update={"axiom_definitions": SAMPLE_AXIOM_ITEMS}
    )

    assert result.axiom_definitions is not None
    assert len(result.axiom_definitions) == 2
    assert result.reality_definitions is None


def test_evaluation_result_with_reality_definitions_only(
    minimal_evaluation_result: EvaluationResult,
) -> None:
    """Test EvaluationResult with only reality definitions."""
    result = minimal_evaluation_result.model_copy(
        update={"reality_definitions": SAMPLE_REALITY_ITEMS}
    )

    assert result.axiom_definitions is None
    assert result.reality_definitions is not None
    assert len(result.reality_definitions) == 2


def test_evaluation_result_with_both_definitions(
    minimal_evaluation_result: EvaluationResult,
) -> None:
    """Test EvaluationResult with both axiom and reality definitions."""
    result = minimal_evaluation_result.model_copy(
        update={
            "axiom_definitions": SAMPLE_AXIOM_ITEMS,
            "reality_definitions": SAMPLE_REALITY_ITEMS,
        }
    )

    assert result.axiom_definitions is not None
    assert len(result.axiom_definitions) == 2
    assert result.reality_definitions is not None
    assert len(result.reality_definitions) == 2


def test_evaluation_result_with_empty_definitions(
    minimal_evaluation_result: EvaluationResult,
) -> None:
    """Test EvaluationResult with empty definition lists."""
    result = minimal_evaluation_result.model_copy(
        update={"axiom_definitions": [], "reality_definitions": []}
    )

    assert result.axiom_definitions is not None
    assert len(result.axiom_definitions) == 0
    assert result.reality_definitions is not None
    assert len(result.reality_definitions) == 0


def test_evaluation_result_serialization_with_definitions(
    minimal_evaluation_result: EvaluationResult,
) -> None:
    """Test EvaluationResult serializes correctly with definitions."""
    result = minimal_evaluation_result.model_copy(
        update={
            "axiom_definitions": SAMPLE_AXIOM_ITEMS,
            "reality_definitions": SAMPLE_REALITY_ITEMS,
        }
    )
    data = result.model_dump()

    assert "axiom_definitions" in data
    assert "reality_definitions" in data
    assert len(data["axiom_definitions"]) == 2
    assert len(data["reality_definitions"]) == 2
    assert data["axiom_definitions"][0]["id"] == "A-001"
    assert data["reality_definitions"][0]["id"] == "R-001"


def test_evaluation_result_serialization_without_definitions(
    minimal_evaluation_result: EvaluationResult,
) -> None:
    """Test EvaluationResult serializes correctly without definitions."""
    data = minimal_evaluation_result.model_dump()

    assert data["axiom_definitions"] is None
    assert data["reality_definitions"] is None


def test_evaluation_result_json_roundtrip_with_definitions(
    minimal_evaluation_result: EvaluationResult,
) -> None:
    """Test EvaluationResult JSON roundtrip with definitions."""
    original = minimal_evaluation_result.model_copy(
        update={
            "axiom_definitions": SAMPLE_AXIOM_ITEMS,
            "reality_definitions": SAMPLE_REALITY_ITEMS,
        }
    )
    json_str = original.model_dump_json()
    restored = EvaluationResult.model_validate_json(json_str)

    assert original.axiom_definitions is not None
    assert restored.axiom_definitions is not None
    assert len(restored.axiom_definitions) == len(original.axiom_definitions)
    assert restored.axiom_definitions[0].id == original.axiom_definitions[0].id

    assert restored.reality_definitions is not None
    assert len(restored.reality_definitions) == 2


def test_evaluation_result_json_roundtrip_without_definitions(
    minimal_evaluation_result: EvaluationResult,
) -> None:
    """Test EvaluationResult JSON roundtrip without definitions."""
    json_str = minimal_evaluation_result.model_dump_json()
    restored = EvaluationResult.model_validate_json(json_str)

    assert restored.axiom_definitions is None
    assert restored.reality_definitions is None


def test_evaluation_result_excludes_none_definitions_in_json(
    minimal_evaluation_result: EvaluationResult,
) -> None:
    """Test that None definitions can be excluded from JSON output."""
    data = minimal_evaluation_result.model_dump(exclude_none=True)

    assert "axiom_definitions" not in data
    assert "reality_definitions" not in data
