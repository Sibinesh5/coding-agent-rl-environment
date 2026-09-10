# Model Evaluation and Analysis

## Evaluation Protocol

I evaluated the task using two different AI coding models. Each run started from a fresh copy of the unmodified `environment/repo` directory.

The model received only the candidate repository and the task instructions. It did not receive the reference solution or verifier implementation. After the model finished, I ran the deterministic verifier against the returned repository without manually repairing the model's changes.

Five independent runs were performed for each model. Every run used a fresh chat/session and a fresh repository copy so that earlier attempts could not influence later results.

## Models

| Label | Exact model/version | Agent harness | Runs | Successful | Stumped |
|---|---|---|---:|---:|---:|
| Model A | GPT-5.6 Sol | ChatGPT web | 5 | 0 | 0 |
| Model B | Gemini 3.1 Pro | Gemini web | 5 | 0 | 1 |

## Quantitative Results

The raw evaluation data is stored in `analysis/eval_runs.csv`.

The metrics can be reproduced with:

```bash
python analysis/summarize_eval.py analysis/eval_runs.csv
```

Observed results:

| Model | n | Successful | pass@1 | pass@2 | pass@3 | Stump % |
|---|---:|---:|---:|---:|---:|---:|
| GPT-5.6 Sol | 5 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0 |
| Gemini 3.1 Pro | 5 | 0 | 0.0000 | 0.0000 | 0.0000 | 20.0 |

Across all ten runs, one run was classified as stumped, giving an overall stump rate of 10%.

For `n` independent attempts containing `c` successful attempts, pass@k is calculated as:

```text
pass@k = 1 - C(n-c, k) / C(n, k)
```

Because neither model produced a completely verifier-passing candidate in the five-run sample, all reported pass@k values are zero.

## Stump Definition

A run is classified as stumped when it fails to produce a meaningful repository-grounded implementation or fails to reach substantive diagnostic progress.

A run that makes substantial code changes but introduces an ImportError, SyntaxError, missing dependency, or incorrect behavior is counted as a failed attempt rather than a stump.

## Run-Level Results

### Model A — GPT-5.6 Sol

#### Run 1

- Result: Failed
- Verifier outcome: 8 passed, 1 failed
- Stumped: No
- Failure category: Semantic double-apply
- Observation: The implementation handled most reliability requirements but failed the semantic duplicate-completion case. A logically repeated payment completion could still reapply the inventory side effect even though the provider event IDs were different.

#### Run 2

- Result: Failed
- Verifier outcome: 8 passed, 1 failed
- Stumped: No
- Failure category: Other verifier failure
- Observation: The candidate was close to the reference behavior but still failed one verifier case. The exact individual failing case was not preserved in the run notes, so it is intentionally not inferred here.

#### Run 3

- Result: Failed
- Verifier outcome: 8 passed, 1 failed
- Stumped: No
- Failure category: Other verifier failure
- Observation: The candidate again implemented most required behavior but did not achieve a full verifier pass. The exact failed case was not preserved.

#### Run 4

- Result: Failed
- Verifier outcome: 8 passed, 1 failed
- Stumped: No
- Failure category: Other verifier failure
- Observation: The candidate made a substantive repository-level fix and passed eight of nine tests, but one verifier requirement remained unsatisfied. The exact failed case was not preserved.

#### Run 5

- Result: Failed
- Verifier outcome: 8 passed, 1 failed
- Stumped: No
- Failure category: Other verifier failure
- Observation: The final GPT-5.6 Sol attempt again reached eight of nine verifier tests without achieving a complete solution. The exact failed case was not preserved.

### Model B — Gemini 3.1 Pro

#### Run 1

- Result: Failed
- Stumped: No
- Failure category: Regression / API-contract breakage
- Observation: The generated webhook service removed the existing `process_payment_webhook` entry point while `app/main.py` still imported it. Application loading failed with an ImportError before verifier behavior could be exercised.

#### Run 2

- Result: Failed
- Stumped: No
- Failure category: Regression / syntax failure
- Observation: Generated changes introduced invalid Python syntax in `app/main.py`. The application therefore failed to import and could not reach behavioral verification.

#### Run 3

- Result: Failed
- Stumped: No
- Failure category: Regression / dependency failure
- Observation: The solution changed SQLAlchemy configuration to use `sqlite+aiosqlite` but did not add the `aiosqlite` dependency. Application loading failed with `ModuleNotFoundError`.

#### Run 4

- Result: Failed
- Stumped: Yes
- Failure category: Repository-inspection stump
- Observation: The model reported that it could not inspect the supplied repository and instead produced a generic replacement script based on assumptions. Because no usable repository-grounded candidate was produced, the verifier was not run for this attempt.
- Note: This stump may reflect web-harness or input-ingestion limitations as well as model reasoning ability.

#### Run 5

- Result: Failed
- Stumped: No
- Failure category: Regression / schema-contract breakage
- Observation: The generated `app/main.py` imported a nonexistent `WebhookEvent` object from `app.schemas`, causing application import failure.

## Failure Analysis

The two models failed in substantially different ways.

GPT-5.6 Sol consistently reached 8/9 verifier tests. This suggests that the common duplicate-event, ordering, transaction, and regression requirements were largely understood, while the benchmark's more subtle logical-idempotency behavior remained discriminative. In particular, exact provider-event deduplication is not sufficient when two different event IDs describe the same logical completion.

Gemini 3.1 Pro showed a different failure pattern. Four of its five attempts made substantive changes, but those changes caused repository-level regressions such as broken imports, invalid syntax, and undeclared dependencies. One run failed to inspect the repository sufficiently to produce a usable candidate and was therefore classified as stumped.

The results demonstrate why the verifier checks both target behavior and unrelated API regressions. A solution that conceptually addresses webhook reliability is not sufficient if it makes the service unloadable or violates the existing repository contract.

## Interpretation of pass@k

Both models produced zero complete successes in five attempts, so pass@1, pass@2, and pass@3 are all zero for this sample.

This should not be interpreted as proof that the task is unsolvable. The provided reference solution passes all nine deterministic verifier tests. GPT-5.6 Sol also repeatedly reached eight of nine tests, providing evidence that the benchmark distinguishes near-correct implementations from fully correct ones.

The sample size is small, so the pass@k numbers should be treated as measurements for these ten runs rather than estimates of universal model capability.

## Reproducibility Notes

The repository and verifier are deterministic, but the hosted ChatGPT and Gemini web interfaces do not expose full control over model sampling parameters or deterministic seeds.

To reduce cross-run contamination, every attempt used:

- a fresh chat/session;
- a fresh copy of the starting repository;
- identical task instructions;
- no reference solution or verifier implementation;
- no manual repair before grading.

The quantitative source of truth is `analysis/eval_runs.csv`, and `analysis/summarize_eval.py` reproduces the reported pass@k and stump metrics.
