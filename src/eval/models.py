from pydantic import BaseModel, Field

AxiomReferences = list[str]
RealityReferences = list[str]


class Entity(BaseModel):
    """
    Represents a causal relationship between two variables.

    This class models an entity that captures the relationship between a
    trigger (cause) and its consequence (effect). It's typically used to
    represent cause-and-effect relationships in financial analysis, banking
    operations, or risk assessment scenarios.

    Attributes:
        trigger_variable (str): The name of the variable that acts as a trigger
            or cause, typically related to financial behaviors, transactions,
            or banking activities.
        consequence_variable (str): The name of the variable that represents
            the outcome or effect, typically related to financial outcomes,
            risk metrics, or performance indicators.
    Example: High credit utilization significantly increases default risk.
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

    user_query_entities: list[Entity] = Field(
        description="Entities extracted from the user query."
    )
    llm_answer_entities: list[Entity] = Field(
        description="Entities extracted from the LLM answer."
    )
    expected_answer_entities: list[Entity] = Field(
        description="Entities extracted from the expected answer."
    )


class EntityAccuracy(BaseModel):
    """
    Represents the accuracy evaluation for a specific entity.
    """

    entity: Entity = Field(
        description="The entity being evaluated for accuracy."
    )
    reason: str = Field(
        description="Explanation of why this accuracy score was assigned."
    )
    score: float = Field(
        description="Accuracy score for the entity, between 0.0 and 1.0.",
        ge=0.0,
        le=1.0,
    )


class AccuracyEvaluationResults(BaseModel):
    """
    A model for storing accuracy evaluation results for multiple entities.
    """

    entity_accuracies: list[EntityAccuracy] = Field(
        description="List of accuracy evaluations for each entity."
    )
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
        return sum(entity.score for entity in self.entity_accuracies) / len(
            self.entity_accuracies
        )


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


class AxiomReferenceResults(BaseModel):
    """
    A model for storing axiom reference evaluation results.
    """

    references_found: AxiomReferences = Field(
        description="List of axiom references found in the LLM answer."
    )
    references_expected: AxiomReferences = Field(
        description="List of axiom references expected in the answer."
    )
    precision: float = Field(
        description="Precision score for axiom references (0.0 to 1.0).",
        ge=0.0,
        le=1.0,
    )
    recall: float = Field(
        description="Recall score for axiom references, between 0.0 and 1.0.",
        ge=0.0,
        le=1.0,
    )


class RealityReferenceResults(AxiomReferenceResults):
    """
    A model for storing reality reference evaluation results.
    """

    pass


class Metric(BaseModel):
    """
    A data model representing statistical metrics with mean and standard
    deviation.

    Attributes:
        mean (float): The arithmetic mean of the data.
        std (float): The standard deviation of the data.
    """

    mean: float
    std: float


class AccuracyMetric(Metric):
    """
    A metric class for calculating accuracy of predictions.

    This metric computes the accuracy as the fraction of predictions that
    match the true labels. Accuracy is calculated as the number of correct
    predictions divided by the total number of predictions.

    The metric can be used for classification tasks where exact matches
    between predicted and actual values are required.

    Returns:
        float: Accuracy score between 0.0 and 1.0, where 1.0 represents
        perfect accuracy.
    """


class CoverageMetric(Metric):
    """
    A metric class for measuring topic coverage during evaluation.

    This metric tracks the degree to which responses cover expected topics
    or concepts in the evaluation samples. It provides insights into how
    comprehensively the system addresses the relevant subject matter.

    Attributes:
        Inherits all attributes from the base Metric class.

    Methods:
        Inherits all methods from the base Metric class and may override
        specific methods to implement coverage-specific calculations.

    Usage:
        Used to monitor and report topic coverage statistics during
        evaluation workflows.
    """


class AxiomPrecisionMetric(Metric):
    """
    A metric class for measuring axiom reference precision during evaluation.
    """


class AxiomRecallMetric(Metric):
    """
    A metric class for measuring axiom reference recall during evaluation.
    """


class RealityPrecisionMetric(Metric):
    """
    A metric class for measuring reality reference precision during evaluation.
    """


class RealityRecallMetric(Metric):
    """
    A metric class for measuring reality reference recall during evaluation.
    """


class EvaluationSampleInput(BaseModel):
    """
    A data model representing input data for evaluation samples.

    This class defines the structure for evaluation sample inputs used in
    the evaluation process, containing all necessary information to assess
    model performance.

    Attributes:
        id (int): Unique identifier for the evaluation sample.
        query (str): The input question or prompt to be evaluated.
        context (str): Contextual information or background data relevant
            to the query.
        expected_answer (str): The correct or expected response for the
            given query.
        reasoning (list[str]): List of reasoning steps or explanations
            that lead to the expected answer.
        axioms_used (list[str]): List of axioms, rules, or principles
            applied in deriving the expected answer.
        reality_used (list[str]): List of real-world facts or data
            referenced in formulating the expected answer.
    """

    id: int
    query: str
    context: str
    expected_answer: str
    reasoning: list[str]
    axioms_used: AxiomReferences
    reality_used: RealityReferences


class EvaluationSampleOutput(BaseModel):
    """
    Represents the output of an evaluation sample containing input data,
    model response, and metrics.

    This class encapsulates the results of evaluating a single sample,
    including the original input, the language model's response, extracted
    entities, and computed performance metrics.

    Attributes:
        input (EvaluationSampleInput): The original input data used for
            evaluation
        llm_response (str): The response generated by the language model
        entities (EntityExtraction): Entities extracted from the response
        accuracy (AccuracyEvaluationResults): Accuracy score for the
            evaluation sample
        topic_coverage (TopicCoverageEvaluationResults): Topic coverage
            score indicating how well the response covers the expected
            topics
    """

    input: EvaluationSampleInput
    llm_response: str
    entities: EntityExtraction
    accuracy: AccuracyEvaluationResults
    topic_coverage: TopicCoverageEvaluationResults
    axiom_references: AxiomReferenceResults
    reality_references: RealityReferenceResults


class EvaluationResult(BaseModel):
    """
    Represents the complete result of an evaluation run.

    This class encapsulates all outputs and metrics from evaluating a
    model or system, providing a comprehensive view of performance across
    multiple dimensions.

    Attributes:
        evaluation_outputs (list[EvaluationSampleOutput]): A list of
            individual sample evaluation results, containing the detailed
            outputs for each test case.
        accuracy (AccuracyMetric): Metric measuring the correctness of
            predictions or responses across the evaluation dataset.
        topic_coverage (CoverageMetric): Metric measuring how well the
            evaluation spans different topics or categories in the domain.
    """

    evaluation_outputs: list[EvaluationSampleOutput]
    accuracy: AccuracyMetric
    topic_coverage: CoverageMetric
    axiom_precision_metric: AxiomPrecisionMetric
    axiom_recall_metric: AxiomRecallMetric
    reality_precision_metric: RealityPrecisionMetric
    reality_recall_metric: RealityRecallMetric
