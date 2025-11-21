"""Report generation main script."""

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from eval.models import EvaluationResult

logger = logging.getLogger(__name__)


class Report:
    """Handles generation of HTML evaluation reports from JSON data."""

    def __init__(self, data_path: str, output_dir: str | None = None) -> None:
        """Initialize the Report instance.

        Args:
            data_path: Path to the evaluation data JSON file
            output_dir: Output directory for generated files (optional)
        """
        super().__init__()
        self.data_path = Path(data_path).resolve()
        self.output_dir = Path(output_dir).resolve() if output_dir else None
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
                logger.error(
                    "JSON data does not match EvaluationResult schema: %s", e
                )
                error_msg = (
                    f"Invalid evaluation data structure: "
                    f"{e.error_count()} validation error(s). "
                    f"See logs for details."
                )
                raise ValueError(error_msg) from e

            return self.evaluation_data

    def _copy_template_file(
        self, template_dir: Path, filename: str, output_path: Path
    ) -> None:
        """Copy a template file to the output directory.

        Args:
            template_dir: Directory containing template files
            filename: Name of the file to copy
            output_path: Destination directory
        """
        source = template_dir / filename
        destination = output_path / filename
        _ = shutil.copy2(source, destination)

    def generate_report(self) -> None:
        """Generate evaluation report from data.

        Raises:
            FileNotFoundError: If the input JSON file doesn't exist.
            ValueError: If the evaluation data is invalid or empty.
            PermissionError: If unable to create output directory due to
                permissions.
        """
        # Load evaluation data
        _ = self.load_json_data()

        # Determine output directory (paths already resolved in __init__)
        if self.output_dir is None:
            # Use the same directory as the input file
            output_path = self.data_path.parent / "report"
        else:
            output_path = self.output_dir

        # Create output directory
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(
                f"Cannot create output directory {output_path}: {e}"
            ) from e

        # Copy template files
        template_dir = Path(__file__).resolve().parent / "templates"
        self._copy_template_file(template_dir, "styles.css", output_path)
        self._copy_template_file(template_dir, "script.js", output_path)
        self._copy_template_file(template_dir, "index.html", output_path)

        # Generate evaluation data JSON file
        data_file_path = output_path / "evaluation_data.json"
        with open(data_file_path, "w", encoding="utf-8") as data_file:
            json.dump(self.evaluation_data, data_file, indent=2)

        html_file_path = output_path / "index.html"
        logger.info("Report generation complete!")
        logger.info(
            "Open %s in your web browser to view the report.", html_file_path
        )

    @classmethod
    def create_and_generate(
        cls, data_path: str, output_dir: str | None = None
    ):
        """Create a Report instance and generate the report.

        This is a convenience class method that creates an instance and
        immediately generates the report.
        """
        report = cls(data_path, output_dir)
        report.generate_report()


def main():
    """Main entry point for report generation."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )

    parser = argparse.ArgumentParser(description="Generate evaluation reports")
    _ = parser.add_argument(
        "--data_path",
        required=True,
        help="Path to the evaluation data JSON file",
    )
    _ = parser.add_argument(
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
