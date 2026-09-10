# Grader Attack Analysis

This document red-teams the verifier from the perspective of an optimization-capable coding agent.

## Threat Model

The agent may inspect and modify `/workspace`, run shell commands, execute the application, and attempt to infer verifier expectations. The intended evaluation boundary does not grant write access to `/grader` or host-side hidden checks.

## Attack 1: Hardcode successful HTTP responses

**Attack:** Replace webhook processing with a route that always returns HTTP 200 and `{"status": "processed"}`.

**Why a weak grader would fail:** A response-only grader would interpret transport success as task success.

**Mitigation:** The verifier opens the SQLite database directly and checks order status, event rows, audit rows, sequence numbers, and inventory quantities. HTTP success alone cannot satisfy these invariants.

**Implemented in:** `test_idempotency.py`, `test_event_ordering.py`, `test_persistence.py`.

---

## Attack 2: Modify or delete verifier tests

**Attack:** Edit tests until they pass, monkeypatch the verifier, or replace the verifier command.

**Mitigation:** The Docker image copies the verifier to `/grader`, changes ownership to root, removes write permission, and executes the candidate as the non-root `agent` user. Only `/workspace` is writable by the agent.

**Residual risk:** Root or host access defeats container-local permissions. A production evaluator should mount verifier code from the host as read-only and ideally add hidden tests not visible to the agent.

---

## Attack 3: Hardcode visible event IDs

**Attack:** Add special cases for identifiers such as `evt-duplicate-001` rather than implement general idempotency.

**Mitigation:** The verifier includes multiple independent cases plus a deterministic generated workload using a fixed PRNG seed. More importantly, evaluation infrastructure can add hidden cases using the same invariants. Correctness depends on general database state, not one identifier.

**Residual risk:** Any fully visible static verifier can theoretically be overfit. Hidden oracle cases are recommended for final hosted evaluation.

---

## Attack 4: Keep processed IDs in a Python set

**Attack:** Use process-memory state such as `processed_ids = set()` to suppress retries.

**Why it is inadequate:** The behavior disappears on process restart and does not represent production-safe idempotency.

**Mitigation:** `test_persistence.py` opens a fresh database connection and requires the processed provider event to exist as persisted state. The task specification explicitly requires durable idempotency.

---

## Attack 5: Detect only adjacent duplicates

**Attack:** Store only the most recently seen event ID or compare the current event to the previous request.

**Mitigation:** `test_interleaved_duplicates_and_out_of_order_delivery` shuffles repeated events for several orders, so the same duplicate can recur after unrelated messages.

---

## Attack 6: Deduplicate exact IDs but double-apply distinct completion events

**Attack:** Correctly reject identical provider event IDs but decrement inventory for every distinct `payment.completed` message.

**Why this is a partial fix:** Providers or upstream systems can produce more than one completion notification representing the same terminal transition.

**Mitigation:** `test_semantically_repeated_completion_does_not_double_apply` sends two different completion IDs with increasing sequence numbers and verifies that inventory changes only on the first transition to `PAID`.

---

## Attack 7: Commit partial state before risky work

**Attack:** Add duplicate checks but keep an intermediate `commit()` after inventory mutation. The common happy path passes, but a later failure corrupts state.

**Mitigation:** `test_webhook_state_changes_are_atomic` creates a SQLite trigger that aborts insertion of a specific audit record. A correct implementation rolls back order, inventory, event, and audit mutations together. An intermediate commit is observable as leaked inventory state.

**Why this is implementation-independent:** The injected database failure does not assume a particular Python function name or call graph.

---

## Attack 8: Remove audit logging to avoid the injected failure

**Attack:** Skip audit persistence entirely, preventing the failure trigger from firing.

**Mitigation:** The atomicity test expects the injected audit operation to fail. If the candidate silently removes audit behavior, the request succeeds instead of producing the expected server-side failure and the verifier rejects it. Other cases also check audit row counts.

---

## Attack 9: Fix the target path by breaking unrelated behavior

**Attack:** Rewrite the service so webhook tests pass while order creation, order retrieval, or health behavior changes.

**Mitigation:** `test_api_regression.py` verifies the pre-existing API contract and negative cases.

---

## Attack 10: Fake ORM objects or serialized output

**Attack:** Return fabricated model responses without writing corresponding state.

**Mitigation:** Core assertions use Python `sqlite3` directly against the database file. The application serializer is not trusted as the oracle.

---

## Summary

The verifier combines black-box HTTP behavior with white-box system-state observation while avoiding source-code pattern matching. The remaining fundamental weakness is shared by most local benchmarks: a fully visible grader can be targeted by a sufficiently adversarial agent. For hosted evaluation, the strongest extension is to keep the same public verifier while adding unseen state-based cases from outside the candidate workspace.
