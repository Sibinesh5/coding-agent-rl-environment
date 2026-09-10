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