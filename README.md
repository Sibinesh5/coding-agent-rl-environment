# Coding Agent RL Environment: Reliable Payment Webhook Processing

## Executive Summary

This environment evaluates whether a coding agent can diagnose and repair a realistic distributed-systems failure mode in a FastAPI order service. The starting repository mishandles duplicate and out-of-order payment webhooks, can decrement inventory more than once, and can partially commit state when downstream work fails. A successful agent must reason across API, persistence, transaction, state-machine, and regression boundaries. The deterministic verifier grades persisted system behavior rather than matching source text or a single expected response.

---

## 1. Engineering Design Document

### 1.1 Capability Mapping

The benchmark measures repository-level software engineering rather than isolated algorithmic problem solving. Specifically, it measures whether an agent can:

- inspect an unfamiliar multi-file FastAPI codebase;
- identify idempotency and event-ordering failures;
- reason about persistent state rather than process-local state;
- design safe transaction boundaries across order, inventory, audit, and event records;
- preserve an existing HTTP contract while changing internal implementation;
- distinguish transport success from business-state correctness;
- run tests, interpret failures, and avoid regressions in unrelated endpoints.

The intended solution requires changes across non-contiguous files. The agent is not told which model, service, repository, or database constraint must change.

### 1.2 Environment Logic and Stochasticity

The environment is intentionally deterministic. It does not contact an external payment provider, database service, queue, or network dependency. SQLite is used as the local persistent store so the full lifecycle is self-contained.

The generated interleaved-delivery scenario uses a local `random.Random(1337)` instance. The seed is fixed and isolated from global randomness, while the remaining verifier cases use fixed deterministic inputs. Test cases reset the database before each verifier case. The Docker base image is pinned to an immutable digest and Python dependencies are pinned to exact versions.

This means repeated runs against the same candidate commit produce the same verifier result.

### 1.3 Oracle Strategy: Correct Behavior vs. Correct Output

The HTTP response is not the oracle. A candidate that returns `200 {"status": "processed"}` for every webhook still fails if persisted state is incorrect.

The verifier checks system invariants directly in SQLite:

1. a repeated provider `event_id` is persisted only once;
2. duplicate delivery does not apply inventory effects twice;
3. a distinct but semantically repeated completion does not decrement inventory twice;
4. a late `payment.pending` event cannot regress a paid order;
5. `last_event_sequence` does not move backward;
6. a forced audit-write failure rolls back every related mutation;
7. processed-event state survives a fresh database connection;
8. unrelated health, order-create, and order-read behavior remains intact.

The atomicity test injects a SQLite trigger that deliberately fails a specific audit insert. This tests transaction semantics without depending on the candidate's function names or implementation structure.

### 1.4 Adversarial Analysis

The benchmark assumes an optimization-capable coding agent may attempt to satisfy the grader without implementing the intended engineering behavior.

The main attack surfaces are:

- hardcoding HTTP responses;
- modifying or deleting verifier tests;
- special-casing visible event IDs;
- storing idempotency state only in memory;
- suppressing audit writes to avoid transaction failures;
- fixing the target behavior while breaking unrelated endpoints;
- detecting only adjacent duplicates instead of true idempotency.

Mitigations are implemented in the verifier and container boundary. Detailed red-team analysis is in `analysis/grader_attacks.md`.

---

## 2. Repository Layout

```text
coding-rl-environment/
├── task/
│   ├── instruction.md
│   └── task.yaml
├── environment/
│   ├── Dockerfile
│   └── repo/
│       ├── app/
│       └── requirements.txt
├── solution/
│   └── reference_solution/
├── tests/
│   └── verifier/
├── analysis/
│   ├── grader_attacks.md
│   ├── model_runs.md
│   ├── eval_runs.csv
│   └── summarize_eval.py
└── README.md
```

---

## 3. Starting-System Failure Modes

The starting service intentionally contains interacting defects rather than a single syntax bug.

| Failure mode | Observable consequence |
|---|---|
| No durable duplicate-event guard | Retried completion decrements inventory repeatedly |
| No event-order check | Late pending event can move `PAID` back to `PENDING` |
| Inventory commit occurs before the rest of webhook work | Downstream failure leaves partial state |
| Event ID lacks uniqueness protection | Duplicate event records are persisted |
| Completion side effect is tied to message arrival, not state transition | Different completion IDs can double-apply inventory changes |

The task prompt exposes symptoms and required invariants, but does not reveal the reference implementation.

---

## 4. Reference Solution Design

The gold solution uses four complementary mechanisms:

1. **Persistent event idempotency**: `ProcessedEvent.event_id` has a database uniqueness constraint and is checked before processing.
2. **Monotonic event ordering**: only events with a higher provider sequence may advance event position.
3. **State-transition idempotency**: inventory is decremented only when the order actually transitions into `PAID`, preventing repeated logical completion from reapplying the side effect.
4. **Single transaction boundary**: inventory, order, event, and audit mutations are committed together. No intermediate commit occurs before audit persistence.

A stale but previously unseen event is recorded for observability while its state mutation is ignored.

---

## 5. Verifier Design

The verifier contains nine deterministic tests grouped by risk:

| Group | Purpose |
|---|---|
| API regression | Preserve health and order API behavior |
| Idempotency | Reject exact duplicate and semantic double-apply solutions |
| Event ordering | Reject state regression and adjacent-only duplicate logic |
| Atomicity | Reject partial commits using an injected database failure |
| Persistence | Reject in-memory-only idempotency approaches |

### Why the verifier uses raw SQL

The grader reads key state with Python's `sqlite3` module instead of trusting application response objects. This reduces the ability of a candidate to fake the expected result through serialization or route-level hardcoding.

### Writable boundary

During container execution:

- `/workspace` is owned by the non-root `agent` user and is writable;
- `/grader` is owned by root and made read-only;
- the container runs as the non-root `agent` user.

The candidate therefore receives a writable repository but cannot normally mutate the verifier directory.

---

## 6. Reproducibility

### Build

From the repository root:

```bash
docker build -f environment/Dockerfile -t coding-rl-webhook-task .
```

### Verify the intentionally broken starting state

```bash
docker run --rm coding-rl-webhook-task
```

A correct benchmark should report verifier failures for the starting repository.

### Verify the reference solution locally without Docker

```bash
python tests/verifier/verify.py --target solution/reference_solution
```

Expected result:

```text
9 passed
```

### Verify a candidate workspace

```bash
TARGET_REPO=/path/to/candidate python tests/verifier/verify.py --target /path/to/candidate
```

---

## 7. Negative Testing Strategy

The verifier intentionally rejects several partial fixes:

- adding only `if order.status == "PAID": return` fails true event-id persistence expectations;
- checking only the previous event fails interleaved duplicate cases;
- storing a Python `set()` of processed IDs fails persistence inspection;
- always returning HTTP 200 fails database-state assertions;
- deduplicating exact IDs while decrementing on every distinct completion fails semantic-repeat testing;
- committing inventory before audit/event persistence fails the injected-trigger rollback test;
- deleting audit logging fails the atomicity scenario because the expected injected failure never occurs;
- broad rewrites that break order creation/read endpoints fail regression tests.

---

## 8. Security and Grader-Hardening Assumptions

No benchmark can be fully secure against an agent with unrestricted host/root access. The threat model is an agent that can edit the assigned repository and execute normal development commands inside the container, but cannot modify the host-side evaluation harness.

The supplied Docker boundary demonstrates this separation by running the candidate as non-root and mounting/copying the verifier into a root-owned read-only location. Production benchmark infrastructure should additionally execute hidden verifier cases from outside the candidate image or mount them read-only at evaluation time.

---

## 9. Model Evaluation Protocol

The assignment requires at least two distinct models and pass@k analysis. Real model outcomes must be measured; they must not be fabricated.

For each model:

1. restore the exact starting repository;
2. start a clean environment;
3. provide only `task/instruction.md` and normal repository access;
4. record the complete agent trace or a faithful action log;
5. run the same deterministic verifier;
6. label the run pass/fail;
7. label whether the run was stumped according to the definition below;
8. repeat enough times to estimate pass@k.

### Stump definition

A run is **stumped** if it terminates without making a meaningful code change or without reaching substantive repository/test-driven diagnostic progress. Syntax-only edits, formatting changes, or repeatedly inspecting the same files without a concrete hypothesis do not count as progress.

### Measured Results

| Model | Runs | Successful | pass@1 | pass@2 | pass@3 | Stump % |
|---|---:|---:|---:|---:|---:|---:|
| GPT-5.6 Sol | 5 | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0 |
| Gemini 3.1 Pro | 5 | 0 | 0.0000 | 0.0000 | 0.0000 | 20.0 |

Detailed run-level analysis is available in `analysis/model_runs.md`.

### pass@k

For `n` independent runs with `c` successful runs:

```text
pass@k = 1 - C(n-c, k) / C(n, k)
```

The included `analysis/summarize_eval.py` calculates pass@k and stump percentage from `analysis/eval_runs.csv`.

---

## 10. Expected Failure Categories for Model Analysis

Useful qualitative categories include:

- notices duplicate retry but misses out-of-order delivery;
- adds event-id deduplication but misses semantic double completion;
- implements ordering but leaves intermediate commits;
- uses in-memory idempotency instead of durable persistence;
- overfits to visible examples;
- changes the API contract;
- fails to inspect database semantics;
- gets stumped before forming a repository-level hypothesis.

These categories should be used to explain quantitative pass@k results in `analysis/model_runs.md`.

---

## 11. Originality

This task was designed specifically for this submission around a synthetic webhook-processing lifecycle. It is not copied from an existing public coding benchmark or LeetCode-style problem. The service, injected failure oracle, task wording, and verifier scenarios are purpose-built for this environment.
