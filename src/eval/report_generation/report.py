"""Report generation main script."""

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from eval.metrics.models import EvaluationResult

logger = logging.getLogger(__name__)


class Report:
    """Handles generation of HTML evaluation reports from JSON data."""

    def __init__(self, data_path: str, output_dir: str | None = None):
        """Initialize the Report instance.

        Args:
            data_path: Path to the evaluation data JSON file
            output_dir: Output directory for generated files (optional)
        """
        self.data_path = data_path
        self.output_dir = output_dir
        self.evaluation_data: dict[str, Any] = {}

    def load_json_data(self) -> dict[str, Any]:
        """Load evaluation data from JSON file.

        Expected JSON structure matching EvaluationResult model output.

        Raises:
            ValueError: If the JSON file is empty, contains no data,
                or has invalid structure.
        """
        with open(self.data_path, encoding="utf-8") as file:
            data = json.load(file)
            if not data:
                raise ValueError("Evaluation data cannot be empty")

            # Validate structure using Pydantic model_validate
            try:
                validated_model = EvaluationResult.model_validate(data)
                self.evaluation_data = validated_model.model_dump()

                logger.info(
                    "Evaluation data validated: %d evaluation outputs",
                    len(self.evaluation_data["evaluation_outputs"]),
                )
            except ValidationError as e:
                logger.error("JSON data does not match EvaluationResult schema: %s", e)
                raise ValueError(
                    f"Invalid evaluation data structure: {e.error_count()} "
                    f"validation error(s). See logs for details."
                ) from e

            return self.evaluation_data

    def generate_report(self):
        """Generate evaluation report from data.

        Raises:
            FileNotFoundError: If the input JSON file doesn't exist.
            ValueError: If the evaluation data is invalid or empty.
            PermissionError: If unable to create output directory due to permissions.
        """
        # Load evaluation data
        self.load_json_data()

        # Determine output directory
        data_path = Path(self.data_path)
        if self.output_dir is None:
            # Use the same directory as the input file
            output_path = data_path.parent / "report"
        else:
            output_path = Path(self.output_dir)

        # Create output directory
        try:
            output_path.mkdir(exist_ok=True)
        except PermissionError as e:
            raise PermissionError(
                f"Cannot create output directory {output_path}: {e}"
            ) from e

        # Copy CSS file (no template rendering needed)
        template_dir = Path(__file__).parent / "templates"
        css_source = template_dir / "styles.css"
        css_file_path = output_path / "styles.css"
        shutil.copy2(css_source, css_file_path)

        # Copy JavaScript file (no template rendering needed)
        js_source = template_dir / "script.js"
        js_file_path = output_path / "script.js"
        shutil.copy2(js_source, js_file_path)

        # Generate evaluation data JSON file
        data_file_path = output_path / "evaluation_data.json"
        with open(data_file_path, "w", encoding="utf-8") as data_file:
            json.dump(self.evaluation_data, data_file, indent=2)

        # Copy HTML file (no template rendering needed)
        html_source = template_dir / "index.html"
        html_file_path = output_path / "index.html"
        shutil.copy2(html_source, html_file_path)

        logger.info("Report generation complete!")
        logger.info("Open %s in your web browser to view the report.", html_file_path)

    @classmethod
    def create_and_generate(cls, data_path: str, output_dir: str | None = None):
        """Create a Report instance and generate the report.

        This is a convenience class method that creates an instance and
        immediately generates the report.
        """
        report = cls(data_path, output_dir)
        report.generate_report()


def main():
    """Main entry point for report generation."""
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Generate evaluation reports")
    parser.add_argument(
        "--data_path", required=True, help="Path to the evaluation data JSON file"
    )
    parser.add_argument(
        "--output_dir",
        help=(
            "Output directory for generated files "
            "(default: same directory as input + '/report')"
        ),
    )

    args = parser.parse_args()
    Report.create_and_generate(args.data_path, args.output_dir)


if __name__ == "__main__":
    main()
