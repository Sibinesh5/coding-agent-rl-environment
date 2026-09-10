# Model Evaluation and Analysis

## Evaluation Protocol

I evaluated the task using two different AI coding models. Each run started from a fresh copy of the unmodified `environment/repo` directory.

The model received only the candidate repository and the task instructions. It did not receive the reference solution or verifier implementation. After the model finished, I ran the deterministic verifier against the returned repository without manually repairing the model's changes.

I performed five independent runs for each model. A new chat and a fresh repository copy were used for every run so that previous attempts could not influence later results.

## Models

| Label | Exact model/version | Agent harness | Runs | Successful | Stumped |
|---|---|---|---:|---:|---:|
| Model A | GPT-5.6 Sol | ChatGPT web | 5 | 0 | 0 |
| Model B | Gemini 3.1 Pro | Gemini web | 5 | 0 | 1 |

Replace `Gemini 3.1 Pro` with the exact model name displayed in Gemini.

## Quantitative Results

The raw results are stored in `analysis/eval_runs.csv`.

I calculated pass@k using:

```bash
python analysis/summarize_eval.py analysis/eval_runs.csv