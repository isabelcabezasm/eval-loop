# Constitutional Q&A Agent

A Q&A agent for queries, grounded on a constitutional framework. The system
combines three key elements:

- **Constitution**: A static "school of thought" document defining axioms and
  principles that govern the company
- **Reality**: The current state of the world and factual context
- **Question**: User queries that may include hypothetical scenarios,
  potentially overriding aspects of reality or constitution for reasoning
  purposes

The agent leverages Azure OpenAI to provide responses that are consistent with
the constitutional framework while adapting to the given context and
hypothetical scenarios.

## Example Use Case

The agent demonstrates the constitutional framework concept through the banking
domain. In this framework, the "Constitution" is intended to be stable
(unchanging principles), while "Reality" is dynamic (reflecting the current
state of the world):

- **Constitution (stable)**: Company principles that remain constant (e.g., for
  our banking domain:  "Political instability disrupts markets and investor
  confidence")
- **Reality (dynamic)**: Current indicators that change over time (e.g., for
  our banking domain "Current inflation rate in Switzerland is 2.1% as of Q3
  2024")
- **Questions**: Queries from the user, that the Q&A agent should answer
  combining principles with current conditions (e.g., "How might borrowing
  costs be affected for someone seeking a mortgage in Switzerland?")

## Development Environment

This project supports **VS Code Dev Containers** for a consistent development
environment with all dependencies pre-configured.

## Quick Start

**Using Dev Containers (Recommended)**:
1. Open the project in VS Code
1. Reopen in Container when prompted
1. Copy environment template: `cp .env.template .env`
1. Edit `.env` with your Azure OpenAI credentials
1. Run a sample query: `uv run python samples/basic_qa.py`

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



