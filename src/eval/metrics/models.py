from pydantic import BaseModel, Field


class Entity(BaseModel):
    """
    Represents a causal relationship between two variables.

    This class models an entity that captures the relationship between a
    trigger (cause) and its consequence (effect). It's typically used to
    represent cause-and-effect relationships in behavioral analysis, habit
    tracking, or outcome measurement scenarios.

    Attributes:
        trigger_variable (str): The name of the variable that acts as a trigger
            or cause, typically related to habits, activities, or input
            factors.
        consequence_variable (str): The name of the variable that represents
            the outcome or effect, typically related to results, effects, or
            output measures.
    Example: Tobacco use significantly increases mortality risk.
    """

    trigger_variable: str = Field(
        description=(
            "The name of the variable, related with habits, activities, ..."
        )
    )
    consequence_variable: str = Field(
        description=(
            "The name of the variable, related with outcomes, effects, ..."
        )
    )


class EntityExtraction(BaseModel):
    """
    A model for storing extracted entities from different sources in an
    evaluation context.
    """

    user_query_entities: list[Entity] = Field(description="Entities extracted from the user query.")
    llm_answer_entities: list[Entity] = Field(description="Entities extracted from the LLM answer.")
    expected_answer_entities: list[Entity] = Field(description="Entities extracted from the expected answer.")


class EntityAccuracy(BaseModel):
    """
    Represents the accuracy evaluation for a specific entity.
    """

    entity: str = Field(description="The entity being evaluated for accuracy.")
    reason: str = Field(description="Explanation of why this accuracy score was assigned.")
    score: float = Field(
        description="Accuracy score for the entity, between 0.0 and 1.0.",
        ge=0.0,
        le=1.0,
    )


class AccuracyEvaluationResults(BaseModel):
    """
    A model for storing accuracy evaluation results for multiple entities.
    """

    entity_accuracies: list[EntityAccuracy] = Field(description="List of accuracy evaluations for each entity.")
    accuracy_mean: float = Field(
        description=(
            "Overall accuracy score across all entities, between 0.0 and 1.0."
        ),
        ge=0.0,
        le=1.0,
    )

    def calculate_accuracy_mean(self) -> float:
        """
        Calculate the mean accuracy score across all entities.
        """
        if not self.entity_accuracies:
            return 0.0
        return sum(entity.score for entity in self.entity_accuracies) / len(self.entity_accuracies)


class TopicCoverageEvaluationResults(BaseModel):
    """
    A model for storing topic coverage evaluation results.

    This model evaluates how well the generated answer covers the expected
    topics by comparing entities between expected and generated content. It
    focuses on recall (coverage) rather than precision.
    """

    reason: str = Field(
        description=(
            "Detailed explanation of the coverage analysis, "
            "including exact matches, approximate matches, "
            "and missing entities."
        )
    )
    coverage_score: float = Field(
        description=(
            "Coverage score representing the percentage of "
            "expected entities present in generated entities, "
            "between 0.0 and 1.0."
        ),
        ge=0.0,
        le=1.0,
    )
