"""Tests for the Report class in report_generation module."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import mock_open, patch

import pytest

from eval.report_generation.report import Report


@pytest.fixture
def sample_evaluation_data() -> dict[str, Any]:
    """Sample evaluation data matching EvaluationResult format."""
    return {
        "evaluation_outputs": [
            {
                "input": {
                    "id": 1,
                    "query": "What is the capital of France?",
                    "context": "Test context",
                    "expected_answer": "Paris",
                    "reasoning": ["Test reasoning"],
                    "axioms_used": ["AXIOM-001"],
                },
                "llm_response": "The capital of France is Paris.",
                "entities": {
                    "user_query_entities": [
                        {
                            "trigger_variable": "France",
                            "consequence_variable": "capital",
                        }
                    ],
                    "llm_answer_entities": [
                        {
                            "trigger_variable": "France",
                            "consequence_variable": "capital",
                        },
                        {
                            "trigger_variable": "capital city",
                            "consequence_variable": "Paris",
                        },
                    ],
                    "expected_answer_entities": [
                        {
                            "trigger_variable": "France",
                            "consequence_variable": "Paris",
                        }
                    ],
                },
                "accuracy": {
                    "entity_accuracies": [
                        {
                            "entity": {
                                "trigger_variable": "France",
                                "consequence_variable": "capital",
                            },
                            "reason": "Correctly identified relationship",
                            "score": 0.95,
                        }
                    ],
                    "accuracy_mean": 0.95,
                },
                "topic_coverage": {
                    "reason": "Good coverage of expected topics",
                    "coverage_score": 0.9,
                },
            },
            {
                "input": {
                    "id": 2,
                    "query": "What is 2+2?",
                    "context": "Math question",
                    "expected_answer": "4",
                    "reasoning": ["Basic addition"],
                    "axioms_used": [],
                },
                "llm_response": "2+2 equals 4.",
                "entities": {
                    "user_query_entities": [
                        {
                            "trigger_variable": "addition",
                            "consequence_variable": "result",
                        }
                    ],
                    "llm_answer_entities": [
                        {
                            "trigger_variable": "2+2",
                            "consequence_variable": "4",
                        }
                    ],
                    "expected_answer_entities": [
                        {
                            "trigger_variable": "calculation",
                            "consequence_variable": "4",
                        }
                    ],
                },
                "accuracy": {
                    "entity_accuracies": [
                        {
                            "entity": {
                                "trigger_variable": "addition",
                                "consequence_variable": "result",
                            },
                            "reason": "Perfect match",
                            "score": 1.0,
                        }
                    ],
                    "accuracy_mean": 1.0,
                },
                "topic_coverage": {
                    "reason": "Full coverage of expected content",
                    "coverage_score": 1.0,
                },
            },
        ],
        "accuracy": {
            "mean": 0.975,
            "std": 0.025,
        },
        "topic_coverage": {
            "mean": 0.95,
            "std": 0.05,
        },
    }


@pytest.fixture
def temp_json_file(
    tmp_path: Path, sample_evaluation_data: dict[str, Any]
) -> Path:
    """Create a temporary JSON file with sample data."""
    json_file = tmp_path / "test_data.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(sample_evaluation_data, f)
    return json_file


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


# Tests for load_json_data method


def test_load_json_data_successfully(
    temp_json_file: Path, sample_evaluation_data: dict[str, Any]
) -> None:
    """Test successful loading of JSON data."""
    report = Report(data_path=str(temp_json_file))
    loaded_data = report.load_json_data()

    assert loaded_data == sample_evaluation_data
    assert report.evaluation_data == sample_evaluation_data


def test_load_json_data_empty_file(tmp_path: Path) -> None:
    """Test loading empty JSON file raises ValueError."""
    empty_json_file = tmp_path / "empty.json"
    with open(empty_json_file, "w", encoding="utf-8") as f:
        json.dump({}, f)

    report = Report(data_path=str(empty_json_file))

    with pytest.raises(ValueError, match="Evaluation data cannot be empty"):
        _ = report.load_json_data()


def test_load_json_data_file_not_found() -> None:
    """Test loading JSON data when file doesn't exist."""
    report = Report(data_path="/nonexistent/file.json")

    with pytest.raises(FileNotFoundError):
        _ = report.load_json_data()


def test_load_json_data_invalid_json(tmp_path: Path) -> None:
    """Test loading invalid JSON data."""
    invalid_json_file = tmp_path / "invalid.json"
    with open(invalid_json_file, "w", encoding="utf-8") as f:
        _ = f.write("This is not valid JSON {")

    report = Report(data_path=str(invalid_json_file))

    with pytest.raises(json.JSONDecodeError):
        _ = report.load_json_data()


def test_load_json_data_missing_structure_keys(tmp_path: Path) -> None:
    """Test loading JSON data with missing structure keys."""
    incomplete_json_file = tmp_path / "incomplete.json"
    incomplete_data = {"some_key": "some_value"}
    with open(incomplete_json_file, "w", encoding="utf-8") as f:
        json.dump(incomplete_data, f)

    report = Report(data_path=str(incomplete_json_file))

    with pytest.raises(ValueError, match="Invalid evaluation data structure"):
        _ = report.load_json_data()


def test_load_json_data_complete_structure_no_error(
    tmp_path: Path,
) -> None:
    """Test loading JSON data with complete structure succeeds."""
    complete_json_file = tmp_path / "complete.json"
    complete_data: dict[str, Any] = {
        "evaluation_outputs": [],
        "accuracy": {"mean": 0.0, "std": 0.0},
        "topic_coverage": {"mean": 0.0, "std": 0.0},
    }
    with open(complete_json_file, "w", encoding="utf-8") as f:
        json.dump(complete_data, f)

    report = Report(data_path=str(complete_json_file))
    loaded_data = report.load_json_data()

    # Verify data was loaded successfully
    assert loaded_data == complete_data


def test_load_json_data_invalid_evaluation_outputs_type(
    tmp_path: Path,
) -> None:
    """Test that non-list evaluation_outputs raises ValueError."""
    invalid_json_file = tmp_path / "invalid.json"
    invalid_data = {
        "evaluation_outputs": "not a list",
        "accuracy": {"mean": 0.0, "std": 0.0},
        "topic_coverage": {"mean": 0.0, "std": 0.0},
    }
    with open(invalid_json_file, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)

    report = Report(data_path=str(invalid_json_file))

    with pytest.raises(ValueError, match="Invalid evaluation data structure"):
        _ = report.load_json_data()


def test_load_json_data_invalid_accuracy_structure(tmp_path: Path) -> None:
    """Test that accuracy without mean/std raises ValueError."""
    invalid_json_file = tmp_path / "invalid.json"
    invalid_data: dict[str, Any] = {
        "evaluation_outputs": [],
        "accuracy": {"wrong_key": 0.0},
        "topic_coverage": {"mean": 0.0, "std": 0.0},
    }
    with open(invalid_json_file, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)

    report = Report(data_path=str(invalid_json_file))

    with pytest.raises(ValueError, match="Invalid evaluation data structure"):
        _ = report.load_json_data()


def test_generate_report_file_not_found() -> None:
    """Test report generation when input file doesn't exist."""
    report = Report(data_path="/nonexistent/file.json")

    with pytest.raises(FileNotFoundError):
        report.generate_report()


def test_generate_report_with_default_output_dir(
    temp_json_file: Path, sample_evaluation_data: dict[str, Any]
) -> None:
    """Test report generation with default output directory."""
    report = Report(data_path=str(temp_json_file))
    report.generate_report()

    # Check output directory was created
    output_path = temp_json_file.parent / "report"
    assert output_path.exists()
    assert output_path.is_dir()

    # Check all files were created
    assert (output_path / "styles.css").exists()
    assert (output_path / "script.js").exists()
    assert (output_path / "index.html").exists()
    assert (output_path / "evaluation_data.json").exists()

    # Verify evaluation data was written correctly
    with open(output_path / "evaluation_data.json", encoding="utf-8") as f:
        written_data = json.load(f)
    assert written_data == sample_evaluation_data


def test_generate_report_with_custom_output_dir(
    temp_json_file: Path,
    temp_output_dir: Path,
    sample_evaluation_data: dict[str, Any],
) -> None:
    """Test report generation with custom output directory."""
    report = Report(
        data_path=str(temp_json_file), output_dir=str(temp_output_dir)
    )
    report.generate_report()

    # Check all files were created in custom output directory
    assert (temp_output_dir / "styles.css").exists()
    assert (temp_output_dir / "script.js").exists()
    assert (temp_output_dir / "index.html").exists()
    assert (temp_output_dir / "evaluation_data.json").exists()

    # Verify evaluation data was written correctly
    with open(temp_output_dir / "evaluation_data.json", encoding="utf-8") as f:
        written_data = json.load(f)
    assert written_data == sample_evaluation_data


def test_generate_report_creates_output_directory_if_not_exists(
    temp_json_file: Path, tmp_path: Path
) -> None:
    """Test that generate_report creates output directory."""
    output_dir = tmp_path / "new_output_dir"
    assert not output_dir.exists()

    report = Report(data_path=str(temp_json_file), output_dir=str(output_dir))
    report.generate_report()

    assert output_dir.exists()
    assert output_dir.is_dir()


def test_generate_report_permission_error_on_directory_creation(
    temp_json_file: Path,
) -> None:
    """Test that generate_report raises PermissionError."""
    report = Report(
        data_path=str(temp_json_file), output_dir="/root/no_access"
    )

    with patch("eval.report_generation.report.Path.mkdir") as mock_mkdir:
        mock_mkdir.side_effect = PermissionError("Permission denied")

        with pytest.raises(
            PermissionError, match="Cannot create output directory"
        ):
            report.generate_report()


@patch("eval.report_generation.report.shutil.copy2")
def test_generate_report_copies_template_files(
    mock_copy: Any,
    temp_json_file: Path,
    sample_evaluation_data: dict[str, Any],
) -> None:
    """Test that template files are copied correctly."""
    report = Report(data_path=str(temp_json_file))

    # Mock the copy operation to avoid actual file copying
    # We need to mock json.load to return our sample data
    mock_file_content = json.dumps(sample_evaluation_data)
    with patch("eval.report_generation.report.Path.mkdir"):
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with patch("json.load", return_value=sample_evaluation_data):
                with patch("json.dump"):
                    report.generate_report()

    # Verify copy2 was called for CSS, JS, and HTML files
    assert mock_copy.call_count == 3
    # assert the parameters of the calls
    calls = [call.args[0].name for call in mock_copy.call_args_list]
    assert "styles.css" in calls[0]
    assert "script.js" in calls[1]
    assert "index.html" in calls[2]


def test_generate_report_handles_existing_output_directory(
    temp_json_file: Path, temp_output_dir: Path
) -> None:
    """Test that generate_report works with existing output directory."""
    # Create a dummy file in output directory
    dummy_file = temp_output_dir / "dummy.txt"
    _ = dummy_file.write_text("dummy content")

    report = Report(
        data_path=str(temp_json_file), output_dir=str(temp_output_dir)
    )
    report.generate_report()

    # Check that dummy file still exists (directory wasn't cleared)
    assert dummy_file.exists()
    # Check that new files were created
    assert (temp_output_dir / "evaluation_data.json").exists()


def test_create_and_generate_with_output_dir(
    temp_json_file: Path, temp_output_dir: Path
) -> None:
    """Test create_and_generate with custom output directory."""
    Report.create_and_generate(
        data_path=str(temp_json_file), output_dir=str(temp_output_dir)
    )
    assert (temp_output_dir / "evaluation_data.json").exists()


def test_create_and_generate_loads_data(
    temp_json_file: Path, sample_evaluation_data: dict[str, Any]
) -> None:
    """Test that create_and_generate loads the evaluation data."""
    Report.create_and_generate(data_path=str(temp_json_file))

    output_path = temp_json_file.parent / "report"
    assert (output_path / "styles.css").exists()
    assert (output_path / "script.js").exists()
    assert (output_path / "index.html").exists()
    assert (output_path / "evaluation_data.json").exists()


def test_full_report_generation_workflow(
    temp_json_file: Path, sample_evaluation_data: dict[str, Any]
) -> None:
    """Test complete workflow from initialization to generation."""
    # Create report instance
    report = Report(data_path=str(temp_json_file))

    # Load data
    loaded_data = report.load_json_data()
    assert loaded_data == sample_evaluation_data

    # Generate report
    report.generate_report()

    # Verify output
    output_path = temp_json_file.parent / "report"
    assert output_path.exists()

    # Verify all files exist and have content
    assert (output_path / "styles.css").stat().st_size > 0
    assert (output_path / "script.js").stat().st_size > 0
    assert (output_path / "index.html").stat().st_size > 0

    with open(output_path / "evaluation_data.json", encoding="utf-8") as f:
        final_data = json.load(f)
    assert final_data == sample_evaluation_data

    # Verify report object state (data_path is now a resolved Path object)
    assert report.data_path == temp_json_file.resolve()
    assert report.evaluation_data == sample_evaluation_data

    # Verify file permissions and types
    assert (
        output_path.stat().st_mode & 0o777 >= 0o755
    )  # Directory is readable/executable
    for file_name in [
        "styles.css",
        "script.js",
        "index.html",
        "evaluation_data.json",
    ]:
        file_path = output_path / file_name
        assert file_path.is_file()
        assert not file_path.is_dir()
        assert file_path.stat().st_size > 0
