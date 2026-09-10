import csv
import math
import sys
from collections import defaultdict
from pathlib import Path


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "pass", "passed"}:
        return True
    if normalized in {"0", "false", "no", "n", "fail", "failed"}:
        return False
    raise ValueError(f"unrecognized boolean value: {value!r}")


def pass_at_k(n: int, c: int, k: int) -> float:
    if k > n:
        return float("nan")
    if n - c < k:
        return 1.0
    return 1.0 - (math.comb(n - c, k) / math.comb(n, k))


def main(path: str) -> int:
    groups = defaultdict(list)
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if not row["passed"].strip() or not row["stumped"].strip():
                continue
            groups[row["model"]].append(
                (parse_bool(row["passed"]), parse_bool(row["stumped"]))
            )

    if not groups:
        print("No completed runs found.")
        return 1

    print("model,n,c,pass@1,pass@2,pass@3,stump_pct")
    for model, runs in sorted(groups.items()):
        n = len(runs)
        c = sum(passed for passed, _ in runs)
        stumped = sum(flag for _, flag in runs)
        values = []
        for k in (1, 2, 3):
            score = pass_at_k(n, c, k)
            values.append("NA" if math.isnan(score) else f"{score:.4f}")
        print(f"{model},{n},{c},{values[0]},{values[1]},{values[2]},{100 * stumped / n:.1f}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python summarize_eval.py analysis/eval_runs.csv")
    raise SystemExit(main(sys.argv[1]))
