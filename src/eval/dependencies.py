from functools import cache

from core.dependencies import azure_chat_openai
from core.paths import root
from eval.llm_evaluator.qa_eval_engine import QAEvalEngine


@cache
def qa_eval_engine() -> QAEvalEngine:
    system_prompt = (
        root() / "src/eval/llm_evaluator/prompts/system_prompt.md"
    ).read_text()

    return QAEvalEngine(
        agent=azure_chat_openai().create_agent(instructions=system_prompt)
    )
