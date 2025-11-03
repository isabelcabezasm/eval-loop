# Constitutional Q&A Agent

A Q&A agent for health insurance queries, grounded on a constitutional framework. The system combines three key elements:

- **Constitution**: A static "school of thought" document defining axioms and principles that govern the domain
- **Reality**: The current state of the world and factual context
- **Question**: User queries that may include hypothetical scenarios, potentially overriding aspects of reality or constitution for reasoning purposes

The agent leverages Azure OpenAI to provide responses that are consistent with the constitutional framework while adapting to the given context and hypothetical scenarios.

## Development Environment

This project supports **VS Code Dev Containers** for a consistent development environment with all dependencies pre-configured.

## Quick Start

**Using Dev Containers (Recommended)**:
1. Open the project in VS Code
2. Reopen in Container when prompted
3. Edit `.env` with your Azure OpenAI credentials
4. Run a sample query: `uv run python samples/basic_qa.py`

**Manual Setup**:
1. Copy environment template: `cp .env.template .env`
2. Edit `.env` with your Azure OpenAI credentials
3. Install dependencies: `uv sync`
4. Run a sample query: `uv run python samples/basic_qa.py`

## Project Structure

- `src/core/` - Core QA engine and Azure OpenAI integration
- `src/eval/` - Evaluation experiments and baselines
- `data/` - Constitution and evaluation datasets
- `tests/` - Unit tests



