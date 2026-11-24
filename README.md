# Day-Planner Agent (practice project)

A small, throwaway project for learning **function/tool calling** by writing the agent loop by hand.
It is **not** a portfolio piece. The major agentic project comes after this one.

- **Roadmap stage covered:** Stage 4 (Function/Tool Calling + Structured Outputs)
- **Next stages (on the major project, not this one):** Stage 5 MCP, Stage 6 LangGraph, then onward
- **Time-box:** about one week (start date: 2026-11-21). If it runs past that, cut scope, don't extend.
- **Status:** not started

---

## 1. What it does

You type a request such as:

> I'm cycling in Pune tomorrow morning and spending ₹2,000. What's the weather, and what's that in USD?

The agent decides which tools to call, runs them, feeds the results back to the model, and returns a final answer
(and, in later steps, a validated JSON verdict).

## 2. Learning goals

1. Understand and hand-write the full tool-calling loop: model requests a tool, you execute it, you return the result, the model continues.
2. Design tool schemas and descriptions, and see how they change the model's choices.
3. Handle chained calls, parallel calls, and failures (bad arguments, unknown tools, API errors, quota exhaustion, runaway loops).
4. Understand side-effect tools and human confirmation.
5. Tell structured output apart from tool calls.
6. Run the same code on more than one free provider and observe where behavior differs.
7. Rewrite the same tools in PydanticAI to see what a framework removes.

## 3. Architecture

```
User question
     |
     v
Agent loop  (src/dayplanner/loop.py, hand-written)
  model -> requests tool(s) -> you execute -> return results -> model continues
     |                                  |
     |                 +----------------+------------------+
     v                 v                v                  v
Final answer      geocode_city     get_forecast     convert_currency
(validated JSON)  (Open-Meteo)     (Open-Meteo)     (ExchangeRate-API)
                       calculate (local)    save_plan (local file, confirm first)
```

Design rules:
- The model never sees API keys. Keys live in `.env` and are read only inside tool code.
- Every tool returns a string or JSON-serializable dict, and **errors are returned as data** (never raised into the loop) so the model can react.
- The loop has a hard `MAX_ITERATIONS` cap.
- The LLM client is created in one place (`llm.py`) so swapping provider means changing env vars only.

## 4. Tech stack

| Concern | Choice |
|---|---|
| Language / env | Python, managed with `uv` |
| LLM access | `openai` package with a custom `base_url` (OpenAI-compatible endpoints) |
| Primary provider | Groq (free tier), model id pinned in `.env` |
| Second provider | Gemini (OpenAI-compatible endpoint) or OpenRouter, for portability tests |
| Validation | `pydantic` |
| HTTP | `httpx` (with timeouts) |
| Framework rewrite (step 9) | PydanticAI |
| Config | `.env` + `.env.example` |

Provider details change often. Before relying on any base URL, model id, or rate limit below, check the provider's own docs.

## 5. Folder structure

```
day-planner-agent/
├── README.md                  # this file
├── DECISIONS.md               # experiment + decision log (see section 10)
├── pyproject.toml             # uv project file
├── .env.example               # blank template, committed
├── .env                       # real keys, NEVER committed
├── .gitignore                 # must list .env, plans/, __pycache__/, .venv/
├── src/
│   └── dayplanner/
│       ├── __init__.py
│       ├── config.py          # loads env vars, validates they exist
│       ├── llm.py             # builds the OpenAI-compatible client from env
│       ├── loop.py            # the hand-written agent loop + MAX_ITERATIONS
│       ├── schemas.py         # tool JSON schemas + final-answer pydantic model
│       ├── cli.py             # entry point: reads a question, runs the loop
│       └── tools/
│           ├── __init__.py    # tool registry: name -> (schema, function)
│           ├── geocode.py     # geocode_city
│           ├── forecast.py    # get_forecast
│           ├── currency.py    # convert_currency (+ rate cache)
│           ├── calculate.py   # calculate (safe evaluator, no eval())
│           └── save_plan.py   # save_plan (confirmation required)
├── framework/
│   └── pydantic_ai_version.py # step 9: same tools rewritten in PydanticAI
├── experiments/
│   ├── exp01_provider_swap.md
│   ├── exp02_tool_descriptions.md
│   ├── exp03_failing_tool.md
│   ├── exp04_unsupported_request.md
│   └── exp05_rate_cache.md
├── notes/
│   └── concepts.md            # your own explanations, in your own words
├── tests/
│   ├── test_calculate.py
│   ├── test_currency_cache.py
│   └── test_loop_cap.py
└── plans/                     # output of save_plan, gitignored
```

## 6. Tools

| # | Tool | Inputs | External service | Key needed | Notes |
|---|---|---|---|---|---|
| 1 | `geocode_city` | `name` | Open-Meteo Geocoding API | No | Must run before the forecast call |
| 2 | `get_forecast` | `lat`, `lon`, `day` | Open-Meteo Forecast API | No | Returns temperature, rain chance, wind |
| 3 | `convert_currency` | `amount`, `from_code`, `to_code` | ExchangeRate-API | Yes | Cache rates; check `result` field in JSON for errors such as `quota-reached` |
| 4 | `calculate` | `expression` | none (local) | No | Safe evaluator; never use `eval()` |
| 5 | `save_plan` | `text` | local file in `plans/` | No | Side effect: requires a confirmation prompt first |

Endpoints (confirm against current docs before coding):
- Open-Meteo: free for non-commercial use, no API key, data under CC BY 4.0. Attribution ("Weather data by Open-Meteo.com") should appear next to displayed data.
- ExchangeRate-API: free plan is about 1,500 requests/month with daily rate updates. Pattern: `https://v6.exchangerate-api.com/v6/<KEY>/latest/USD` and `.../pair/<BASE>/<TARGET>/<AMOUNT>`.

## 7. Setup

1. `uv init` and add dependencies: `openai`, `httpx`, `pydantic`, `python-dotenv`.
2. Create `.gitignore` **before** the first commit, with at least: `.env`, `plans/`, `.venv/`, `__pycache__/`.
3. Create `.env.example` (blank values, committed) and copy it to `.env` (real values, never committed):

```
LLM_BASE_URL=            # e.g. the provider's OpenAI-compatible endpoint (verify in docs)
LLM_API_KEY=
LLM_MODEL=               # pin the exact model id and record it in DECISIONS.md
EXCHANGE_RATE_API_KEY=
MAX_ITERATIONS=6
```

4. Never paste a key into a prompt, a tool schema, a log line, a chat, or a public repo. If one leaks, regenerate it.

## 8. Build steps (check off as you go)

| Step | What you build | Concept learned | Done |
|---|---|---|---|
| 1 | Skeleton, `.env`, one plain chat call | Provider setup, `base_url` swap | [ ] |
| 2 | `convert_currency` + the loop | The request, execute, return cycle | [ ] |
| 3 | `geocode_city` + `get_forecast` | Chained calls (geocode must come first) | [ ] |
| 4 | Two-city comparison prompt | Parallel tool calls (handle every tool_call in a response, not just the first) | [ ] |
| 5 | `calculate` | Why tools beat LLM arithmetic | [ ] |
| 6 | Failure handling | Bad args, unknown tool, API error, `quota-reached`, `MAX_ITERATIONS` | [ ] |
| 7 | `save_plan` + confirmation | Side-effect tools and human-in-the-loop | [ ] |
| 8 | Final JSON verdict, validated with pydantic | Structured output vs tool calls | [ ] |
| 9 | Same tools in PydanticAI | What a framework removes; try `FallbackModel` across two providers | [ ] |

Working rule for each step: write the code yourself, explain every line out loud (or in `notes/concepts.md`), then run one experiment before moving on.

## 9. Failure-handling matrix (step 6)

| Failure | Expected behavior |
|---|---|
| Model calls a tool that doesn't exist | Return an error string listing valid tool names; do not crash |
| Model sends malformed or missing arguments | Validate with pydantic; return the validation error as the tool result |
| External API timeout or HTTP error | Return a short error message; no stack trace |
| ExchangeRate-API returns `result: error` (e.g. `quota-reached`) | Surface the error code to the model; do not retry blindly |
| Model keeps requesting tools forever | Stop at `MAX_ITERATIONS` and return a clear message |
| User declines `save_plan` confirmation | Return "user declined" as the tool result |
| Provider rate limit (HTTP 429) | Back off or fail clearly; record in DECISIONS.md which provider and when |

## 10. Experiments and DECISIONS.md

Each experiment gets a file in `experiments/` and a short entry in `DECISIONS.md`.

| # | Experiment | What to record |
|---|---|---|
| 1 | Same prompt on two providers | Where tool calling differs or breaks, with the exact error or behavior |
| 2 | Vague vs precise tool descriptions | Tool-selection accuracy over a fixed set of prompts (for example 10 runs each) |
| 3 | A deliberately failing tool | Does the model recover, retry, or loop? |
| 4 | A request no tool can handle | Does it answer honestly or invent a tool? |
| 5 | Rate cache vs fresh call each time | Requests used against the 1,500/month quota |

`DECISIONS.md` entry template:

```
## <date> - <decision title>
- Context: what I was trying to do
- Options considered:
- Chosen: and why
- Evidence: the actual run or output that supports it
- Provider / pinned model id:
```

Only log what you observed in a real run. Do not log guesses.

## 11. Test prompts (fixed set, reuse across experiments)

1. "Convert 2000 INR to USD."
2. "What's the weather in Pune tomorrow morning?"
3. "Compare tomorrow's weather in Pune and Hyderabad."
4. "I'm cycling in Pune tomorrow and spending 2000 INR. Weather, and how much is that in USD?"
5. "What is 15% of 2000 plus 340?"
6. "Save a short plan for tomorrow's ride." (triggers confirmation)
7. "What's the weather in Atlantis?" (geocode failure)
8. "Book me a flight to Goa." (no tool exists)

## 12. Definition of done

- [ ] All five tools work through the loop you wrote yourself.
- [ ] It runs on at least two providers by changing only `.env`.
- [ ] Every failure in section 9 is handled and has a test or a logged run.
- [ ] Final answer is validated JSON.
- [ ] `DECISIONS.md` has at least five entries, each backed by an actual run.
- [ ] You can explain every line of `loop.py` without looking at it.
- [ ] PydanticAI version works and you have written down what it removed and what it hid.
- [ ] No secrets in the repo history (check before pushing).

## 13. Risks

- **Free-tier rate limits** will interrupt long sessions, and providers change limits without notice. Check your own account's limits.
- **Free models may call tools poorly.** That is useful data. Log it instead of switching models silently.
- **Quota burn:** the exchange API's monthly cap is easy to exhaust while debugging. Cache.
- **Model churn:** free-tier model availability can change. Pin the exact model id and record it.
- **Scope creep:** this is a learning project. Do not add features beyond the build steps.

## 14. What this project is not

- Not a resume project (weather and currency conversion are toy domains).
- Not a framework comparison. The framework step is only to see what a framework removes.
- Not the major project. The major project will integrate MCP, LangGraph, memory, evaluation, and guardrails in a separate repo or codebase.

## 15. After this project

1. Review `DECISIONS.md` and `notes/concepts.md`.
2. Share the major project idea and map it onto Stages 4 to 12.
3. Carry over what worked: the loop structure, the failure-handling matrix, the `.env` discipline, and the DECISIONS.md habit.

## 16. References

- Anthropic tool-use tutorial (hand-written loop, then tool runner): docs for the Claude Platform, "Build a tool-using agent".
- PydanticAI model providers and `FallbackModel`: ai.pydantic.dev
- Open-Meteo docs: open-meteo.com
- ExchangeRate-API docs: exchangerate-api.com/docs
- Roadmap: `THE Definitive Roadmap - Agentic AI Engineer (Fresher, India)`, Stage 4