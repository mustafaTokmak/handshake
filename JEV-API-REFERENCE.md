# Jev on OpenRouter — verified API reference

Discovered empirically 2026-09-19 (endpoint not in OpenRouter model-listing docs; error messages were the spec). Working demo: `jev_demo.py`.

## Endpoint

- `POST https://openrouter.ai/api/alpha/decisions`
- Header: `Authorization: Bearer $OPENROUTER_API_KEY`
- **`/api/v1/chat/completions` does NOT work** — returns 400: *"typesafe/jev-1.13 is a decisions model and cannot be used with the chat/completions endpoint."*
- Model ids: `typesafe/jev-1.13` (resolves to dated build `typesafe/jev-1.13-20260917` in the response), 32K context, provider `TypeSafe`.

## Request

```json
{
  "model": "typesafe/jev-1.13",
  "state": "<unstructured state, one big string>",
  "questions": {
    "same_customer":  { "type": "noul",   "instructions": "Is the ticket requester the same person as the customer of record?" },
    "customer_mood":  { "type": "choice", "instructions": "Classify the customer's tone",
                        "criteria": { "polite": "friendly wording", "angry": "hostile wording", "neutral": "flat factual wording" } },
    "blast_radius":   { "type": "score",  "instructions": "If this action is wrong, how bad is it?",
                        "criteria": [ { "level": 1, "description": "trivial, easily reversed" },
                                      { "level": 10, "description": "irreversible financial loss" } ] }
  }
}
```

Schema gotchas (each learned from a 400):

- Every question object needs `instructions` (string | record | array all accepted).
- `noul` = binary probability. No extra fields.
- `choice` needs `criteria` as a **record** (class name → description). Returns selected class + per-class probabilities + confidence.
- `score` needs `criteria` as an **array** of `{level, description}`. Returns an ordinal float (expected level, not the argmax index) + probabilities + confidence.
- Multiple questions in one request = one fan-out call, all answered together. Independents in parallel; returns marginals, not a joint.

## Response

```json
{
  "model": "typesafe/jev-1.13-20260917",
  "answers": {
    "same_customer":  { "type": "noul",   "noul": 0.08 },
    "customer_mood":  { "type": "choice", "choice": "neutral",
                        "probabilities": { "neutral": 1.0, "polite": 0.0, "angry": 0.0 }, "confidence": 0.99 },
    "blast_radius":   { "type": "score",  "score": 0.96,
                        "probabilities": { "0": 1.0 }, "confidence": 0.92 }
  },
  "usage": { "input_tokens": 332, "output_tokens": 61, "cost": 0.000021 },
  "id": "gen-dec-…", "provider": "TypeSafe"
}
```

- `score` is a float (e.g. `0.96`) — expected level on the criteria scale, NOT an integer index. Pydantic field must be `float`.
- `confidence` is distribution concentration, NOT P(correct). For exposure use a named class probability, never `1 - confidence`.
- Some answers in the wild have `conf` field names — validate raw output before trusting field names across builds.

## Observed performance (2026-09-19, single smoke runs)

- 4 judgements, one call: **374–483ms**, `$0.000021` (~$21/M calls if token size holds).
- Correctly separated the planted mismatch: `same_customer p=0.08` on `sam@acme.io` vs `robert@acme.com`.
- Pricing sanity: roughly 280–340 input tokens for this state+bundle size.

## Pydantic parsing (see jev_demo.py)

Discriminated union on `type` works cleanly:

```python
class Noul(BaseModel):  type: Literal["noul"];   noul: float
class Choice(BaseModel): type: Literal["choice"]; choice: str; probabilities: dict[str, float]; confidence: float
class Score(BaseModel): type: Literal["score"];  score: float; probabilities: dict[str, float]; confidence: float
Answer = TypeAdapter(Union[Noul, Choice, Score])
```

## Keys

- Key lives in `.env` in this directory (`OPENROUTER_API_KEY=…`). Never commit, never echo.

## LLM contrast (for the demo split screen)

- Fast/cheap LLM on OpenRouter: `openai/gpt-5.6-luna` ($0.20/M in, $1.20/M out, 1M ctx) — same questions via `chat/completions` + `response_format` json_schema. Expect seconds vs Jev's ~400ms.
