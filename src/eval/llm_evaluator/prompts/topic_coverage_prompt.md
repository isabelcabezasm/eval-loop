Compare the following two list of entities:
Expected entities: {expected_entities}
Generated entities: {generated_entities}

Your task is to:

1. If either list is empty:
   - State clearly which list is empty.
   - Set coverage score to 1 if both lists are empty (since there’s nothing expected and nothing generated).
   - Set coverage score to 0 if expected_entities is not empty and generated_entities is empty.
   - Set coverage score to 0 if expected_entities is empty and generated_entities is not empty.
   - Provide a reason explaining the situation (e.g., "No entities were expected" or "No entities were generated").
   - Do NOT attempt synonym matching in this case.

2. Otherwise:
   - Check entities in both lists, considering synonyms or equivalent terms (e.g., "interest rate" ≈ "policy rate").
   - In the reason, explain which entities matched exactly, which matched approximately, and which were missing.
   - Calculate coverage score:
       * 1 for exact or accurate synonym matches
       * 0.5 for inaccurate synonyms
       * 0 for missing
   - Coverage score = (sum of match scores) / (number of expected entities).