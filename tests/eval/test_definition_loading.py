"""
Tests for axiom and reality definition loading functions.

This module tests:
- load_axiom_definitions: loading axioms from constitution.json
- load_reality_definitions: loading reality items from reality.json
- Error handling for missing files and invalid JSON
- calculate_stats integration with definitions
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from eval.eval import (
    calculate_stats,
    load_axiom_definitions,
    load_reality_definitions,
)
from eval.models import (
    AccuracyEvaluationResults,
    AxiomItem,
    AxiomReferenceResults,
    Entity,
    EntityAccuracy,
    EntityExtraction,
    EvaluationSampleInput,
    EvaluationSampleOutput,
    RealityItem,
    RealityReferenceResults,
    TopicCoverageEvaluationResults,
)

# =============================================================================
# Type Aliases
# =============================================================================

LoaderFunc = Callable[[Path], list[AxiomItem] | list[RealityItem]]
ItemType = type[AxiomItem] | type[RealityItem]

# =============================================================================
# Test Data
# =============================================================================

VALID_AXIOM_JSON: list[dict[str, str]] = [
    {"id": "A-001", "description": "First axiom description."},
    {"id": "A-002", "description": "Second axiom description."},
]

VALID_REALITY_JSON: list[dict[str, str]] = [
    {"id": "R-001", "description": "First reality description."},
    {"id": "R-002", "description": "Second reality description."},
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_output() -> EvaluationSampleOutput:
    """Create a minimal EvaluationSampleOutput for testing."""
    return EvaluationSampleOutput(
        input=EvaluationSampleInput(
            id=1,
            query="Test query",
            context="Test context",
            expected_answer="Expected answer",
            reasoning=["Step 1"],
            axioms_used=["A-001"],
            reality_used=["R-001"],
        ),
        llm_response="LLM response text",
        entities=EntityExtraction(
            user_query_entities=[
                Entity(
                    trigger_variable="var1",
                    consequence_variable="consequence1",
                )
            ],
            llm_answer_entities=[
                Entity(
                    trigger_variable="var2",
                    consequence_variable="consequence2",
                )
            ],
            expected_answer_entities=[
                Entity(
                    trigger_variable="var3",
                    consequence_variable="consequence3",
                )
            ],
        ),
        accuracy=AccuracyEvaluationResults(
            entity_accuracies=[
                EntityAccuracy(
                    entity=Entity(
                        trigger_variable="var1",
                        consequence_variable="consequence1",
                    ),
                    reason="Accuracy reason",
                    score=0.8,
                )
            ],
            accuracy_mean=0.8,
        ),
        topic_coverage=TopicCoverageEvaluationResults(
            reason="Coverage reason",
            coverage_score=0.9,
        ),
        axiom_references=AxiomReferenceResults(
            references_found=["A-001"],
            references_expected=["A-001"],
            precision=1.0,
            recall=1.0,
        ),
        reality_references=RealityReferenceResults(
            references_found=["R-001"],
            references_expected=["R-001"],
            precision=1.0,
            recall=1.0,
        ),
    )


# =============================================================================
# Parametrized Tests for Definition Loading Functions
# =============================================================================


@pytest.mark.parametrize(
    ("loader_func", "valid_json", "item_type", "id_prefix"),
    [
        (load_axiom_definitions, VALID_AXIOM_JSON, AxiomItem, "A-"),
        (load_reality_definitions, VALID_REALITY_JSON, RealityItem, "R-"),
    ],
    ids=["axiom", "reality"],
)
def test_load_definitions_valid_file(
    tmp_path: Path,
    loader_func: LoaderFunc,
    valid_json: list[dict[str, str]],
    item_type: ItemType,
    id_prefix: str,
) -> None:
    """Test loading definitions from a valid JSON file."""
    test_file = tmp_path / "test.json"
    _ = test_file.write_text(json.dumps(valid_json))

    result = loader_func(test_file)

    assert len(result) == 2
    assert all(isinstance(item, item_type) for item in result)
    assert result[0].id == f"{id_prefix}001"
    assert result[1].id == f"{id_prefix}002"


@pytest.mark.parametrize(
    "loader_func",
    [load_axiom_definitions, load_reality_definitions],
    ids=["axiom", "reality"],
)
def test_load_definitions_missing_file(
    tmp_path: Path,
    loader_func: LoaderFunc,
) -> None:
    """Test that loading from a missing file raises FileNotFoundError."""
    missing_file = tmp_path / "nonexistent.json"

    with pytest.raises(FileNotFoundError):
        _ = loader_func(missing_file)


@pytest.mark.parametrize(
    "loader_func",
    [load_axiom_definitions, load_reality_definitions],
    ids=["axiom", "reality"],
)
def test_load_definitions_invalid_json(
    tmp_path: Path,
    loader_func: LoaderFunc,
) -> None:
    """Test that loading invalid JSON raises JSONDecodeError."""
    invalid_file = tmp_path / "invalid.json"
    _ = invalid_file.write_text("not valid json {{{")

    with pytest.raises(json.JSONDecodeError):
        _ = loader_func(invalid_file)


@pytest.mark.parametrize(
    ("loader_func", "invalid_json", "expected_field"),
    [
        (load_axiom_definitions, [{"id": "A-001"}], "description"),
        (load_reality_definitions, [{"id": "R-001"}], "description"),
        (load_axiom_definitions, [{"description": "desc"}], "id"),
        (load_reality_definitions, [{"description": "desc"}], "id"),
    ],
    ids=[
        "axiom_missing_description",
        "reality_missing_description",
        "axiom_missing_id",
        "reality_missing_id",
    ],
)
def test_load_definitions_missing_required_field(
    tmp_path: Path,
    loader_func: LoaderFunc,
    invalid_json: list[dict[str, Any]],
    expected_field: str,
) -> None:
    """Test that missing required field raises ValidationError."""
    test_file = tmp_path / "test.json"
    _ = test_file.write_text(json.dumps(invalid_json))

    with pytest.raises(ValidationError) as exc_info:
        _ = loader_func(test_file)

    assert expected_field in str(exc_info.value)


@pytest.mark.parametrize(
    ("loader_func", "invalid_json", "expected_field"),
    [
        (
            load_axiom_definitions,
            [{"id": "", "description": "desc"}],
            "id",
        ),
        (
            load_reality_definitions,
            [{"id": "", "description": "desc"}],
            "id",
        ),
        (
            load_axiom_definitions,
            [{"id": "A-001", "description": ""}],
            "description",
        ),
        (
            load_reality_definitions,
            [{"id": "R-001", "description": ""}],
            "description",
        ),
    ],
    ids=[
        "axiom_empty_id",
        "reality_empty_id",
        "axiom_empty_description",
        "reality_empty_description",
    ],
)
def test_load_definitions_empty_required_field(
    tmp_path: Path,
    loader_func: LoaderFunc,
    invalid_json: list[dict[str, str]],
    expected_field: str,
) -> None:
    """Test that empty required field raises ValidationError."""
    test_file = tmp_path / "test.json"
    _ = test_file.write_text(json.dumps(invalid_json))

    with pytest.raises(ValidationError) as exc_info:
        _ = loader_func(test_file)

    assert expected_field in str(exc_info.value)


@pytest.mark.parametrize(
    "loader_func",
    [load_axiom_definitions, load_reality_definitions],
    ids=["axiom", "reality"],
)
def test_load_definitions_empty_array(
    tmp_path: Path,
    loader_func: LoaderFunc,
) -> None:
    """Test loading an empty JSON array returns empty list."""
    test_file = tmp_path / "test.json"
    _ = test_file.write_text("[]")

    result = loader_func(test_file)

    assert result == []


# =============================================================================
# Tests for Default Path Loading
# =============================================================================


@pytest.mark.parametrize(
    ("loader_func", "item_type", "id_prefix", "first_item_content"),
    [
        (
            load_axiom_definitions,
            AxiomItem,
            "A-",
            "Political instability",
        ),
        (
            load_reality_definitions,
            RealityItem,
            "R-",
            "inflation rate",
        ),
    ],
    ids=["axiom", "reality"],
)
def test_load_definitions_default_path(
    loader_func: Callable[[], list[AxiomItem] | list[RealityItem]],
    item_type: ItemType,
    id_prefix: str,
    first_item_content: str,
) -> None:
    """Test loading from default path uses actual data files."""
    result = loader_func()

    assert len(result) > 0
    assert all(isinstance(item, item_type) for item in result)
    assert result[0].id == f"{id_prefix}001"
    assert first_item_content in result[0].description


# =============================================================================
# Tests for JSON Structure Compatibility
# =============================================================================


@pytest.mark.parametrize(
    ("loader_func", "id_prefix"),
    [
        (load_axiom_definitions, "A-"),
        (load_reality_definitions, "R-"),
    ],
    ids=["axiom", "reality"],
)
def test_definitions_match_actual_structure(
    loader_func: Callable[[], list[AxiomItem] | list[RealityItem]],
    id_prefix: str,
) -> None:
    """Test that loaded definitions have expected structure."""
    items = loader_func()

    for item in items:
        assert item.id.startswith(id_prefix)
        assert len(item.id) == 5  # e.g., "A-001" or "R-001"
        assert len(item.description) > 0


# =============================================================================
# Tests for calculate_stats with Definitions
# =============================================================================


def test_calculate_stats_includes_axiom_definitions(
    sample_output: EvaluationSampleOutput,
) -> None:
    """Test that calculate_stats includes axiom definitions in result."""
    axiom_defs = [
        AxiomItem(id="A-001", description="Axiom 1 description"),
        AxiomItem(id="A-002", description="Axiom 2 description"),
    ]

    result = calculate_stats([sample_output], axiom_definitions=axiom_defs)

    assert result.axiom_definitions is not None
    assert len(result.axiom_definitions) == 2
    assert result.axiom_definitions[0].id == "A-001"
    assert result.axiom_definitions[1].id == "A-002"


def test_calculate_stats_includes_reality_definitions(
    sample_output: EvaluationSampleOutput,
) -> None:
    """Test that calculate_stats includes reality definitions in result."""
    reality_defs = [
        RealityItem(id="R-001", description="Reality 1 description"),
        RealityItem(id="R-002", description="Reality 2 description"),
    ]

    result = calculate_stats([sample_output], reality_definitions=reality_defs)

    assert result.reality_definitions is not None
    assert len(result.reality_definitions) == 2
    assert result.reality_definitions[0].id == "R-001"
    assert result.reality_definitions[1].id == "R-002"


def test_calculate_stats_includes_both_definitions(
    sample_output: EvaluationSampleOutput,
) -> None:
    """Test that calculate_stats includes both definitions."""
    axiom_defs = [AxiomItem(id="A-001", description="Axiom 1")]
    reality_defs = [RealityItem(id="R-001", description="Reality 1")]

    result = calculate_stats(
        [sample_output],
        axiom_definitions=axiom_defs,
        reality_definitions=reality_defs,
    )

    assert result.axiom_definitions is not None
    assert result.reality_definitions is not None
    assert len(result.axiom_definitions) == 1
    assert len(result.reality_definitions) == 1


def test_calculate_stats_without_definitions(
    sample_output: EvaluationSampleOutput,
) -> None:
    """Test that calculate_stats works without definitions."""
    result = calculate_stats([sample_output])

    assert result.axiom_definitions is None
    assert result.reality_definitions is None
    # Verify other metrics are still calculated
    assert result.accuracy.mean == 0.8
    assert result.topic_coverage.mean == 0.9


def test_calculate_stats_empty_results_with_definitions() -> None:
    """Test that calculate_stats handles empty results with definitions."""
    axiom_defs = [AxiomItem(id="A-001", description="Axiom 1")]
    reality_defs = [RealityItem(id="R-001", description="Reality 1")]

    result = calculate_stats(
        [],
        axiom_definitions=axiom_defs,
        reality_definitions=reality_defs,
    )

    assert result.axiom_definitions is not None
    assert result.reality_definitions is not None
    assert len(result.evaluation_outputs) == 0
    # Metrics should be 0.0 for empty results
    assert result.accuracy.mean == 0.0


def test_calculate_stats_serialization_with_definitions(
    sample_output: EvaluationSampleOutput,
) -> None:
    """Test that result with definitions serializes correctly to JSON."""
    axiom_defs = [AxiomItem(id="A-001", description="Axiom 1")]
    reality_defs = [RealityItem(id="R-001", description="Reality 1")]

    result = calculate_stats(
        [sample_output],
        axiom_definitions=axiom_defs,
        reality_definitions=reality_defs,
    )

    # Serialize to JSON and verify structure
    json_output = result.model_dump_json()
    assert '"axiom_definitions"' in json_output
    assert '"reality_definitions"' in json_output
    assert '"A-001"' in json_output
    assert '"R-001"' in json_output
