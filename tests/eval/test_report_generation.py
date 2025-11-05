"""Tests for the Report class in report_generation module."""

import json
from unittest.mock import mock_open, patch

import pytest

from eval.report_generation.report import Report


@pytest.fixture
def sample_evaluation_data():
    """Sample evaluation data for testing."""
    return {
        "metadata": {
            "timestamp": "2024-11-04T12:00:00",
            "model": "gpt-4",
        },
        "results": [
            {
                "question": "What is the capital of France?",
                "answer": "Paris",
                "score": 0.95,
            },
            {
                "question": "What is 2+2?",
                "answer": "4",
                "score": 1.0,
            },
        ],
    }


@pytest.fixture
def temp_json_file(tmp_path, sample_evaluation_data):
    """Create a temporary JSON file with sample data."""
    json_file = tmp_path / "test_data.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(sample_evaluation_data, f)
    return json_file


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


# Tests for load_json_data method


def test_load_json_data_successfully(temp_json_file, sample_evaluation_data):
    """Test successful loading of JSON data."""
    report = Report(data_path=str(temp_json_file))
    loaded_data = report.load_json_data()

    assert loaded_data == sample_evaluation_data
    assert report.evaluation_data == sample_evaluation_data


def test_load_json_data_empty_file(tmp_path):
    """Test loading empty JSON file raises ValueError."""
    empty_json_file = tmp_path / "empty.json"
    with open(empty_json_file, "w", encoding="utf-8") as f:
        json.dump({}, f)

    report = Report(data_path=str(empty_json_file))

    with pytest.raises(ValueError, match="Evaluation data cannot be empty"):
        report.load_json_data()


def test_load_json_data_file_not_found():
    """Test loading JSON data when file doesn't exist."""
    report = Report(data_path="/nonexistent/file.json")

    with pytest.raises(FileNotFoundError):
        report.load_json_data()


def test_load_json_data_invalid_json(tmp_path):
    """Test loading invalid JSON data."""
    invalid_json_file = tmp_path / "invalid.json"
    with open(invalid_json_file, "w", encoding="utf-8") as f:
        f.write("This is not valid JSON {")

    report = Report(data_path=str(invalid_json_file))

    with pytest.raises(json.JSONDecodeError):
        report.load_json_data()


def test_generate_report_file_not_found():
    """Test report generation when input file doesn't exist raises FileNotFoundError."""
    report = Report(data_path="/nonexistent/file.json")

    with pytest.raises(FileNotFoundError):
        report.generate_report()


def test_generate_report_with_default_output_dir(
    temp_json_file, sample_evaluation_data
):
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
    temp_json_file, temp_output_dir, sample_evaluation_data
):
    """Test report generation with custom output directory."""
    report = Report(data_path=str(temp_json_file), output_dir=str(temp_output_dir))
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
    temp_json_file, tmp_path
):
    """Test that generate_report creates output directory if it doesn't exist."""
    output_dir = tmp_path / "new_output_dir"
    assert not output_dir.exists()

    report = Report(data_path=str(temp_json_file), output_dir=str(output_dir))
    report.generate_report()

    assert output_dir.exists()
    assert output_dir.is_dir()


@patch("eval.report_generation.report.shutil.copy2")
def test_generate_report_copies_template_files(
    mock_copy, temp_json_file, sample_evaluation_data
):
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
    temp_json_file, temp_output_dir
):
    """Test that generate_report works with existing output directory."""
    # Create a dummy file in output directory
    dummy_file = temp_output_dir / "dummy.txt"
    dummy_file.write_text("dummy content")

    report = Report(data_path=str(temp_json_file), output_dir=str(temp_output_dir))
    report.generate_report()

    # Check that dummy file still exists (directory wasn't cleared)
    assert dummy_file.exists()
    # Check that new files were created
    assert (temp_output_dir / "evaluation_data.json").exists()


def test_create_and_generate_with_output_dir(temp_json_file, temp_output_dir):
    """Test create_and_generate with custom output directory."""
    result = Report.create_and_generate(
        data_path=str(temp_json_file), output_dir=str(temp_output_dir)
    )

    assert isinstance(result, Report)
    assert result.data_path == str(temp_json_file)
    assert result.output_dir == str(temp_output_dir)
    assert (temp_output_dir / "evaluation_data.json").exists()


def test_create_and_generate_loads_data(temp_json_file, sample_evaluation_data):
    """Test that create_and_generate loads the evaluation data."""
    result = Report.create_and_generate(data_path=str(temp_json_file))

    assert isinstance(result, Report)
    assert result.data_path == str(temp_json_file)
    assert result.evaluation_data == sample_evaluation_data

    output_path = temp_json_file.parent / "report"
    assert (output_path / "styles.css").exists()
    assert (output_path / "script.js").exists()
    assert (output_path / "index.html").exists()
    assert (output_path / "evaluation_data.json").exists()


def test_full_report_generation_workflow(temp_json_file, sample_evaluation_data):
    """Test complete workflow from initialization to report generation."""
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

    # Verify report object state
    assert report.data_path == str(temp_json_file)
    assert report.evaluation_data == sample_evaluation_data

    # Verify file permissions and types
    assert (
        output_path.stat().st_mode & 0o777 >= 0o755
    )  # Directory is readable/executable
    for file_name in ["styles.css", "script.js", "index.html", "evaluation_data.json"]:
        file_path = output_path / file_name
        assert file_path.is_file()
        assert not file_path.is_dir()
        assert file_path.stat().st_size > 0
