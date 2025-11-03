from eval.main import run_evaluation_with_qa_function


async def generate_answer(*, query: str) -> str:
    print(f"Generating answer for query: {query}")
    return f"Generated answer for: {query}"


def main():
    """
    Main function that runs the experiment_01 evaluation.
    """
    run_evaluation_with_qa_function(generate_answer)


if __name__ == "__main__":
    main()
