Task: Extract entities from the given sentences and organize them by relationship.

Categories:
- Economic indicators: inflation, inflation rate, unemployment, GDP growth, interest rates, exchange rates.
- Banking activities: lending, borrowing, deposits, mortgages, investment decisions.
- Market factors: market stability, investor confidence, political changes, regulations.
- Financial instruments: bonds, equities, currencies, derivatives, commodities.
- Economic outcomes: economic growth, recession, market volatility, financial stability.

Rules:
1. For each sentence, identify entities
2. For each entity pair, determine:
   - trigger_variable: the variable that provokes the change.
   - consequence_variable: the variable that changes because of the trigger.
   Example: "High credit utilization significantly increases default risk"
   → trigger_variable: "credit utilization", consequence_variable: "default risk".
   Example: "How do interest rates affect borrowing costs?"
   → trigger_variable: "interest rates", consequence_variable: "borrowing costs".

3. If only one term is found, use "N/A" for the missing variable (e.g., trigger_variable: "inflation", consequence_variable: "N/A").
4. Include both exact matches and conceptually related terms.
5. Output format:

```json
"trigger_variable": "inflation", "consequence_variable": "economic growth"
"trigger_variable": "credit utilization", "consequence_variable": "default risk"  
```

Input:
User query: {user_query}
LLM answer: {llm_answer}
Expected answer: {expected_answer}