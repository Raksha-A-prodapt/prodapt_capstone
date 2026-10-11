# Feedback and DeepEval workflow

The feedback module records user ratings without changing prompts, models, thresholds, or agent behavior. Negative feedback is marked for deferred evaluation.

## API

`POST /api/feedback`

```json
{
  "response_id": "response-id-from-api",
  "query": "user query",
  "final_response": "displayed answer",
  "rating": "helpful",
  "comment": "optional comment"
}
```

The default database is `feedback/feedback.sqlite3`. Set `FEEDBACK_DB_PATH` to use another location.

## Evaluate flagged responses

From the repository root:

```powershell
.\venv\Scripts\python.exe -m feedback.deepeval_evaluator --limit 10
```

The evaluator reuses `evaluations.aicredits_judge.AICreditsGeminiJudge` and `ai_credits_api_key`, `DEEPEVAL_BASE_URL`, and `DEEPEVAL_MODEL` from `.env`. Missing keys or provider failures are stored as evaluation errors rather than breaking the assistant.
