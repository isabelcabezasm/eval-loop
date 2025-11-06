"""
Run all QA Engine samples.

This script automatically discovers and runs all sample files in the samples directory.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Discover and run all sample files in the samples directory."""
    # Get the samples directory
    samples_dir = Path(__file__).parent

    # Find all Python files except this one
    sample_files = sorted(f for f in samples_dir.glob("*.py") if f.name != "run_all_samples.py")

    if not sample_files:
        print("No sample files found.")
        return

    print(f"Found {len(sample_files)} sample(s) to run:\n")
    for sample_file in sample_files:
        print(f"  - {sample_file.name}")

    print("\n" + "=" * 80)

    # Run each sample
    for i, sample_file in enumerate(sample_files, 1):
        print(f"\n[{i}/{len(sample_files)}] Running {sample_file.name}...")
        print("=" * 80 + "\n")

        result = subprocess.run(
            [sys.executable, str(sample_file)],
            cwd=samples_dir.parent,
            check=False,
        )

        if result.returncode != 0:
            print(f"\n⚠️  {sample_file.name} exited with code {result.returncode}")

        if i < len(sample_files):
            print("\n" + "=" * 80)

    print("\n" + "=" * 80)
    print("All samples completed.")


if __name__ == "__main__":
    main()
