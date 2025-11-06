import argparse
import asyncio

from eval.eval import QuestionAnswerFunction, run_evaluation


def run_evaluation_with_qa_function(
    question_answer_fn: QuestionAnswerFunction,
):
    """
    Reusable main function that parses command line arguments and runs the
    evaluation.

    Args:
        question_answer_fn: The question-answer function to use for evaluation
    """
    parser = argparse.ArgumentParser(
        description="Run evaluation on provided data"
    )
    _ = parser.add_argument(
        "--data_path",
        required=False,
        help=(
            "Path to the data file or directory "
            "(optional, defaults to data/eval_dataset.json)"
        ),
    )

    args = parser.parse_args()

    # Run the async evaluation function
    asyncio.run(
        run_evaluation(
            question_answer_fn=question_answer_fn,
            input_data_path=args.data_path,
        )
    )


def main():
    """
    Default main function with a dummy question-answer function.
    """

    # TODO: For now, we'll need to provide a dummy question_answer_fn
    # This should be properly implemented based on your requirements
    async def dummy_qa_fn(*, query: str) -> str:
        return f"Generated answer for: {query}"

    run_evaluation_with_qa_function(dummy_qa_fn)


if __name__ == "__main__":
    main()
