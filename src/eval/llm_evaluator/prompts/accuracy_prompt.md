This metric measures the accuracy of the predictions in the "generated answer" (e.g.,
interest rates increase / decrease, market stability improves / deteriorates, inflation rises / falls) compared to the ground
truth for these entities: {entity_list}

Evaluate the generated answer by assessing whether the underlying semantics and behaviors 
of the predicted entities match those in the expected answer, regardless of how they are 
specifically expressed. Determine whether the entity's behavior in the generated answer 
aligns with that in the expected answer. (inflation trends, interest rate movements, economic stability, etc)

For each entity in the list:
1. Determine if the entity is mentioned or relevant in both answers
2. Assess if the predicted behavior/outcome matches the expected behavior/outcome
3. Assign an accuracy score between 0.0 and 1.0 (0.0 if no match or absent, 1.0 if perfect match)
4. Provide reasoning for the score

Calculate an overall accuracy as the average of all entity accuracy scores.

Generated answer: {llm_answer}
Expected answer: {expected_answer}

Return the evaluation results for each entity and the overall accuracy score.