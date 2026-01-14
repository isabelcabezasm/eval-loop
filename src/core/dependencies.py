from functools import cache

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from azure.core.credentials import TokenCredential
from azure.identity import AzureCliCredential

from core.axiom_store import load_from_json
from core.paths import root
from core.qa_engine import QAEngine


@cache
def credential() -> TokenCredential:
    """Get credentials for authentication towards Azure."""
    return AzureCliCredential()


@cache
def azure_chat_openai():
    """Get an Azure OpenAI chat client."""
    return AzureOpenAIChatClient(credential=credential())


@cache
def chat_agent() -> ChatAgent:
    """Create the ChatAgent with system prompt."""
    system_prompt = (root() / "src/core/prompts/system_prompt.md").read_text()
    return azure_chat_openai().create_agent(
        name="Constitutional QA Assistant",
        instructions=system_prompt,
        description="AI assistant specialized in banking and economic matters with constitutional grounding"
    )


@cache
def axiom_store():
    """Load the constitutional axioms from JSON data file."""
    return load_from_json((root() / "data/constitution.json").read_text())


@cache
def qa_engine() -> QAEngine:
    """Create the QA Engine with Agent Framework client."""
    return QAEngine(
        agent=chat_agent(),
        axiom_store=axiom_store(),
    )
