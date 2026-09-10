.PHONY: verify-broken verify-reference eval-summary package

verify-broken:
	python tests/verifier/verify.py --target environment/repo

verify-reference:
	python tests/verifier/verify.py --target solution/reference_solution

eval-summary:
	python analysis/summarize_eval.py analysis/eval_runs.csv

package:
	zip -r coding-rl-environment.zip . -x '.git/*' '__pycache__/*' '*.pyc' '.pytest_cache/*' '*.db'
