Compare the following two list of entities:
Expected entities: {expected_entities}
Generated entities: {generated_entities}

Your task is to:

1. Check the entities of both list, consider synonyms or equivalent terms (e.g.,
"interest rate" is equivalent to "policy rate", or "inflation" is equivalent to "price increases"). Add those considerations in the reason property. 

2. Provide a reason
explaining which entities matched exactly, which matched approximately (e.g. inaccurate
synonyms) and which were missing. 

3. Based on the reasoning above, calculate the coverage
score: the percentage of expected entities that are present in the generated entities.
The score should be a float between 0 and 1 (e.g. 1 if it matches, or if the synonym is
accurate, 0.5 if the synonym is inaccurate, and 0 if doesn't match at all)
 