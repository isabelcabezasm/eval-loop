"""Report generation main script."""

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any


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
        """Load evaluation data from JSON file."""
        with open(self.data_path, encoding="utf-8") as file:
            self.evaluation_data = json.load(file)
            return self.evaluation_data

    def generate_report(self):
        """Generate evaluation report from data."""
        print(f"Generating report from data at: {self.data_path}")

        # Check if input file exists
        if not os.path.exists(self.data_path):
            print(f"Error: JSON file '{self.data_path}' not found.")
            return

        # Load evaluation data
        print(f"Loading evaluation data from {self.data_path}...")
        self.load_json_data()

        # Determine output directory
        if self.output_dir is None:
            # Use the same directory as the input file
            input_path = Path(self.data_path)
            output_path = input_path.parent / "report"
        else:
            output_path = Path(self.output_dir)

        # Create output directory
        output_path.mkdir(exist_ok=True)
        print(f"Output directory: {output_path.absolute()}")

        # Copy CSS file (no template rendering needed)
        template_dir = Path(__file__).parent / "templates"
        css_source = template_dir / "styles.css"
        css_file_path = output_path / "styles.css"
        shutil.copy2(css_source, css_file_path)
        print(f"Copied CSS file: {css_file_path}")

        # Copy JavaScript file (no template rendering needed)
        js_source = template_dir / "script.js"
        js_file_path = output_path / "script.js"
        shutil.copy2(js_source, js_file_path)
        print(f"Copied JavaScript file: {js_file_path}")

        # Generate evaluation data JSON file
        data_file_path = output_path / "evaluation_data.json"
        with open(data_file_path, "w", encoding="utf-8") as data_file:
            json.dump(self.evaluation_data, data_file, indent=2)
        print(f"Generated data file: {data_file_path}")

        # Copy HTML file (no template rendering needed)
        html_source = template_dir / "index.html"
        html_file_path = output_path / "index.html"
        shutil.copy2(html_source, html_file_path)
        print(f"Copied HTML file: {html_file_path}")

        print("\nReport generation complete!")
        print(f"Open {html_file_path} in your web browser to view the report.")

    @classmethod
    def create_and_generate(cls, data_path: str, output_dir: str | None = None):
        """Create a Report instance and generate the report.

        This is a convenience class method that creates an instance and
        immediately generates the report.
        """
        report = cls(data_path, output_dir)
        report.generate_report()
        return report


def main():
    """Main entry point for report generation."""
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
