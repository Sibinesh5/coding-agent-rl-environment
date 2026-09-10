# Task: Make Payment Webhook Processing Reliable

The repository contains a FastAPI order service that consumes asynchronous payment webhooks.
Production monitoring has identified consistency problems under realistic delivery conditions:

- payment providers may retry the same event multiple times;
- events can arrive out of order;
- repeated or delayed events can produce incorrect order or inventory state;
- failures during processing can leave related records inconsistent.

Investigate the repository and implement a production-quality fix.

## Requirements

1. Preserve the existing HTTP API contract.
2. Webhook handling must be idempotent for repeated provider events.
3. Delayed or out-of-order events must not regress a valid order state.
4. A logically repeated completion must not decrement inventory more than once.
5. Related state changes must be atomic: a failed webhook must not partially mutate the system.
6. Idempotency information must be persisted, not kept only in process memory.
7. Existing unrelated endpoints must continue to work.
8. Do not modify the verifier.

You may modify application code, database models, and internal service/repository logic as needed.
