"""
Prompt Builder for constitutional AI assistant.

This module provides functions for loading and formatting prompts with
constitution and reality data.
"""

from dataclasses import asdict
from functools import cache

from jinja2 import Environment, FileSystemLoader, Template

from core.axiom_store import AxiomStore
from core.paths import root
from core.reality import RealityStatement


@cache
def _load_template(file: str) -> Template:
    """Load a Jinja2 template from the prompts directory."""
    return Environment(loader=FileSystemLoader(root() / "src/core/prompts")).get_template(file)


def _format_constitution(axiom_store: AxiomStore) -> str:
    """
    Load the constitution template and format it with axiom data.

    Args:
        axiom_store: Storage for axioms/constitution data.

    Returns:
        Formatted constitution text with axioms.
    """
    template = _load_template("constitution.j2")
    axioms = axiom_store.list()
    return template.render(axioms=[asdict(axiom) for axiom in axioms])


def _format_reality(
    reality: list[RealityStatement] | None = None,
) -> str | None:
    """
    Load the reality template and format it with reality statements.

    Args:
        reality: Optional list of reality statements to format.

    Returns:
        Formatted reality text if reality statements are provided,
        None otherwise.
    """
    if not reality:
        return None

    template = _load_template("reality.j2")
    return template.render(
        reality=[asdict(statement) for statement in reality]
    )


def build_user_prompt(
    axiom_store: AxiomStore,
    question: str,
    reality: list[RealityStatement] | None = None,
) -> str:
    """
    Load and format the user prompt with constitution, reality, and question.

    Args:
        axiom_store: Storage for axioms/constitution data.
        question: The user's question to be answered.
        reality: Optional list of reality statements to include in the prompt.

    Returns:
        Formatted user prompt with constitution, reality (if provided),
        and question.
    """
    template = _load_template("user_prompt.j2")

    # Get formatted constitution
    constitution = _format_constitution(axiom_store)

    # Format reality if provided
    formatted_reality = _format_reality(reality)

    # Render template with constitution, reality, and question
    return template.render(constitution=constitution, reality=formatted_reality, question=question)
