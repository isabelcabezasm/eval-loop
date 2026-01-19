import uuid

from core.dependencies import qa_engine
from core.qa_engine import UserSessionId
from eval.main import run_evaluation_with_qa_function


async def generate_answer(*, query: str) -> str:
    """
    Generate an answer for the given query.

    This function asynchronously processes a query and returns a
    generated answer. Currently implements a placeholder that echoes
    the query in the response.

    Args:
        query (str): The input query string to generate an answer for.

    Returns:
        str: A generated answer string based on the input query.

    Example:
        >>> answer = await generate_answer(query="What is Python?")
        >>> print(answer)
        Generated answer for: What is Python?
    """
    print(f"Generating answer for query: {query}")
    # Each evaluation query uses a fresh session (no conversation context)
    session_id = UserSessionId(str(uuid.uuid4()))
    answer = await qa_engine().invoke(question=query, session_id=session_id)
    return answer


def main():
    """
    Main function that runs the baseline evaluation.
    """
    run_evaluation_with_qa_function(generate_answer)


if __name__ == "__main__":
    main()
